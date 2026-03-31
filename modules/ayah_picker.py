"""
ayah_picker.py
──────────────
Randomly selects a short Quran verse (ayah) from Quran.com API v4.
Returns full metadata including Uthmani Arabic text and translation.
"""

import json
import random
import time
from pathlib import Path
from typing import Optional

import requests

from config.settings import (
    QURAN_API_BASE,
    SHORT_SURAH_IDS,
    MAX_RETRIES,
    RETRY_DELAY_SEC,
    PUBLISHED_LOG,
)
from modules.logger import get_logger

log = get_logger("ayah_picker")


# ── helpers ────────────────────────────────────────────────────────────────

def _load_published() -> set[str]:
    """Load the set of already-published ayah keys (surah:ayah)."""
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


def _api_get(url: str, params: dict = None) -> Optional[dict]:
    """GET with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            log.warning(f"API attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
    return None


def _get_surah_info(surah_id: int) -> Optional[dict]:
    data = _api_get(f"{QURAN_API_BASE}/chapters/{surah_id}")
    if data:
        return data.get("chapter")
    return None


def _get_ayah(surah_id: int, ayah_number: int) -> Optional[dict]:
    """Fetch a single ayah with Uthmani text + English translation."""
    params = {
        "translations": "131",   # Dr. Mustafa Khattab (clear English)
        "fields": "text_uthmani,verse_key,chapter_id,verse_number",
    }
    data = _api_get(
        f"{QURAN_API_BASE}/verses/by_key/{surah_id}:{ayah_number}",
        params=params,
    )
    if not data:
        return None
    verse = data.get("verse", {})
    translations = verse.get("translations", [{}])
    translation_text = translations[0].get("text", "") if translations else ""
    # Strip HTML tags from translation
    import re
    translation_text = re.sub(r"<[^>]+>", "", translation_text)

    return {
        "key": f"{surah_id}:{ayah_number}",
        "surah_id": surah_id,
        "ayah_number": ayah_number,
        "arabic_text": verse.get("text_uthmani", ""),
        "translation": translation_text,
        "verse_key": verse.get("verse_key", f"{surah_id}:{ayah_number}"),
    }


def _get_surah_verse_count(surah_id: int) -> int:
    info = _get_surah_info(surah_id)
    if info:
        return info.get("verses_count", 7)
    return 7


# ── public API ──────────────────────────────────────────────────────────────

def pick_ayah(max_attempts: int = 20) -> Optional[dict]:
    """
    Pick a random short ayah that hasn't been published yet.

    Returns a dict with keys:
        key, surah_id, ayah_number, arabic_text, translation, verse_key
    Returns None if no suitable ayah is found after max_attempts.
    """
    published = _load_published()
    candidates = list(SHORT_SURAH_IDS)
    random.shuffle(candidates)

    for _ in range(max_attempts):
        surah_id = random.choice(candidates)
        verse_count = _get_surah_verse_count(surah_id)
        ayah_number = random.randint(1, verse_count)
        key = f"{surah_id}:{ayah_number}"

        if key in published:
            log.info(f"Skipping already-published ayah {key}")
            continue

        ayah = _get_ayah(surah_id, ayah_number)
        if not ayah:
            log.warning(f"Could not fetch ayah {key}, skipping")
            continue

        if not ayah["arabic_text"]:
            log.warning(f"Empty Arabic text for {key}, skipping")
            continue

        log.info(f"Selected ayah: {key} — {ayah['arabic_text'][:50]}…")
        return ayah

    log.error("Could not find a suitable ayah after max attempts")
    return None


def mark_published(ayah_key: str) -> None:
    """Record that this ayah has been published."""
    published = _load_published()
    published.add(ayah_key)
    _save_published(published)
    log.info(f"Marked {ayah_key} as published")
