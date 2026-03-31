"""
caption_generator.py
────────────────────
Caption generator with optional tafsir support.
"""

import json
from pathlib import Path

from config.settings import ENABLE_TAFSIR
from modules.logger import get_logger

log = get_logger("caption_generator")

BASE_HASHTAGS = [
    "#Quran", "#Islam", "#Reminder", "#DailyQuran", "#QuranVerses",
    "#IslamicQuotes", "#Alhamdulillah", "#Sunnah", "#Muslim",
    "#FaithAndReminders", "#QuranDaily", "#قرآن", "#إسلام",
    "#آيات_قرآنية", "#ذكر_الله",
]

_TAFSIR_CACHE: dict[str, str] | None = None
_TAFSIR_PATH = Path(__file__).resolve().parent / "data" / "tafsir_short_ar.json"


def _load_tafsir() -> dict[str, str]:
    global _TAFSIR_CACHE
    if _TAFSIR_CACHE is not None:
        return _TAFSIR_CACHE

    if _TAFSIR_PATH.exists():
        try:
            _TAFSIR_CACHE = json.loads(_TAFSIR_PATH.read_text(encoding="utf-8"))
        except Exception:
            _TAFSIR_CACHE = {}
    else:
        _TAFSIR_CACHE = {}
    return _TAFSIR_CACHE


def _simple_tafsir_fallback(ayah: dict) -> str:
    text = ayah.get("translation") or ayah.get("arabic_text", "")
    text = text.strip()
    if len(text) > 140:
        text = text[:137] + "…"
    return f"المعنى العام: {text}" if text else "المعنى العام: دعوة للتدبر والعمل بالقرآن."


def _build_tafsir_block(ayahs: list[dict]) -> str:
    if not ENABLE_TAFSIR:
        return ""

    tafsir_map = _load_tafsir()
    first_key = ayahs[0].get("key", "")
    tafsir = tafsir_map.get(first_key) or _simple_tafsir_fallback(ayahs[0])
    return f"📌 التفسير:\n{tafsir}"


def _surah_line(ayahs: list[dict]) -> str:
    surah_name = ayahs[0].get("surah_name_ar", "")
    start = ayahs[0].get("ayah_number")
    end = ayahs[-1].get("ayah_number")
    if start == end:
        return f"📖 سورة {surah_name} — آية {start}"
    return f"📖 سورة {surah_name} — الآيات {start} إلى {end}"


def generate_caption(ayah: dict) -> str:
    return generate_caption_for_ayahs([ayah])


def generate_caption_for_ayahs(ayahs: list[dict], reciter_label: str = "مشاري العفاسي") -> str:
    if not ayahs:
        return ""

    arabic_block = "\n".join(a.get("arabic_text", "") for a in ayahs)
    tafsir_block = _build_tafsir_block(ayahs)
    hashtags = " ".join(BASE_HASHTAGS[:9])

    blocks = [
        _surah_line(ayahs),
        arabic_block,
    ]
    if tafsir_block:
        blocks.append(tafsir_block)

    blocks.extend([
        f"🎧 القارئ: {reciter_label}",
        "━━━━━━━━━━━━━━━━",
        hashtags,
    ])

    caption = "\n\n".join(blocks)
    log.info("Caption generated for %s ayah(s)", len(ayahs))
    return caption
