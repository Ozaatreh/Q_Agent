"""
ayah_picker.py
──────────────
Ayah selector with multi-ayah support.

Features:
- Picks 1 ayah (legacy) or a sequential range (2-5 ayahs)
- Ensures all ayahs are from the same surah and in order
- Preserves Uthmani text with harakat/tashkeel
- Caches chapter metadata to reduce API calls
"""

import json
import random
import re
import time
from typing import Optional

import requests

from config.settings import (
    QURAN_API_BASE,
    SHORT_SURAH_IDS,
    MAX_RETRIES,
    RETRY_DELAY_SEC,
    PUBLISHED_LOG,
    ENABLE_MULTI_AYAH,
    MIN_AYAHS_PER_VIDEO,
    MAX_AYAHS_PER_VIDEO,
)
from modules.logger import get_logger

log = get_logger("ayah_picker")

_CHAPTER_CACHE: dict[int, dict] = {}


def _load_published() -> set[str]:
    if PUBLISHED_LOG.exists():
        try:
            data = json.loads(PUBLISHED_LOG.read_text(encoding="utf-8"))
            return set(data.get("published", []))
        except Exception:
            pass
    return set()


def _save_published(published: set[str]) -> None:
    PUBLISHED_LOG.write_text(
        json.dumps({"published": sorted(published)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _api_get(url: str, params: dict | None = None) -> Optional[dict]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = requests.get(url, params=params, timeout=20)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as exc:
            log.warning(f"API attempt {attempt}/{MAX_RETRIES} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
    return None


def _get_surah_info(surah_id: int) -> Optional[dict]:
    if surah_id in _CHAPTER_CACHE:
        return _CHAPTER_CACHE[surah_id]

    data = _api_get(f"{QURAN_API_BASE}/chapters/{surah_id}")
    chapter = data.get("chapter") if data else None
    if chapter:
        _CHAPTER_CACHE[surah_id] = chapter
    return chapter


def _get_surah_verse_count(surah_id: int) -> int:
    info = _get_surah_info(surah_id)
    return int(info.get("verses_count", 7)) if info else 7


def _clean_translation(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _get_ayah(surah_id: int, ayah_number: int) -> Optional[dict]:
    params = {
        "translations": "131",
        "fields": "text_uthmani,verse_key,chapter_id,verse_number",
    }
    data = _api_get(
        f"{QURAN_API_BASE}/verses/by_key/{surah_id}:{ayah_number}",
        params=params,
    )
    if not data:
        return None

    verse = data.get("verse", {})
    chapter = _get_surah_info(surah_id) or {}
    translations = verse.get("translations", [{}])
    translation_text = _clean_translation(translations[0].get("text", "") if translations else "")

    return {
        "key": f"{surah_id}:{ayah_number}",
        "surah_id": surah_id,
        "ayah_number": ayah_number,
        "arabic_text": verse.get("text_uthmani", ""),
        "translation": translation_text,
        "verse_key": verse.get("verse_key", f"{surah_id}:{ayah_number}"),
        "surah_name_ar": chapter.get("name_arabic", ""),
        "surah_name_en": chapter.get("name_simple", ""),
    }


def _pick_sequence_bounds(surah_id: int) -> tuple[int, int]:
    verse_count = _get_surah_verse_count(surah_id)

    if not ENABLE_MULTI_AYAH or verse_count <= 1:
        index = random.randint(1, verse_count)
        return index, 1

    max_len = max(1, min(MAX_AYAHS_PER_VIDEO, verse_count))
    min_len = max(1, min(MIN_AYAHS_PER_VIDEO, max_len))
    sequence_len = random.randint(min_len, max_len)
    start_max = max(1, verse_count - sequence_len + 1)
    start = random.randint(1, start_max)
    return start, sequence_len


def _fetch_sequence(surah_id: int, start_ayah: int, length: int) -> Optional[list[dict]]:
    ayahs: list[dict] = []
    for ayah_number in range(start_ayah, start_ayah + length):
        ayah = _get_ayah(surah_id, ayah_number)
        if not ayah or not ayah.get("arabic_text"):
            return None
        ayahs.append(ayah)
    return ayahs


def pick_ayah(max_attempts: int = 20) -> Optional[dict]:
    """Legacy single-ayah picker for backward compatibility."""
    ayahs = pick_ayahs(max_attempts=max_attempts)
    return ayahs[0] if ayahs else None


def pick_ayahs(max_attempts: int = 20) -> Optional[list[dict]]:
    """Pick a sequential set of ayahs from one surah."""
    published = _load_published()
    surah_candidates = list(SHORT_SURAH_IDS)

    for _ in range(max_attempts):
        surah_id = random.choice(surah_candidates)
        start_ayah, length = _pick_sequence_bounds(surah_id)

        keys = [f"{surah_id}:{idx}" for idx in range(start_ayah, start_ayah + length)]
        if any(key in published for key in keys):
            continue

        ayahs = _fetch_sequence(surah_id, start_ayah, length)
        if not ayahs:
            continue

        log.info(
            "Selected sequence %s (%s ayahs)",
            f"{surah_id}:{start_ayah}-{start_ayah + length - 1}",
            length,
        )
        return ayahs

    log.error("Could not find suitable ayah sequence after max attempts")
    return None


def mark_published(ayah_key: str | list[str]) -> None:
    """Record one ayah key or a list of keys as published."""
    keys = [ayah_key] if isinstance(ayah_key, str) else ayah_key
    published = _load_published()
    published.update(keys)
    _save_published(published)
    log.info("Marked %s ayah(s) as published", len(keys))
