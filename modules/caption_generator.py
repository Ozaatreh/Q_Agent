"""
caption_generator.py
────────────────────
Generates a clean, spiritual Instagram caption for a Quran ayah.
Includes Arabic text snippet, English meaning, surah reference,
and relevant hashtags.
"""

from modules.logger import get_logger

log = get_logger("caption_generator")

# ── Hashtag sets ─────────────────────────────────────────────────────────────

BASE_HASHTAGS = [
    "#Quran", "#Islam", "#Reminder", "#DailyQuran", "#QuranVerses",
    "#IslamicQuotes", "#Alhamdulillah", "#Sunnah", "#Muslim",
    "#FaithAndReminders", "#QuranDaily", "#قرآن", "#إسلام",
    "#آيات_قرآنية", "#ذكر_الله",
]

SURAH_THEMES = {
    1:   ["#AlFatiha", "#OpeningChapter"],
    112: ["#Tawheed", "#Ikhlas", "#Monotheism"],
    113: ["#Protection", "#AlFalaq"],
    114: ["#AnNas", "#Refuge"],
    108: ["#AlKawthar", "#Abundance"],
    103: ["#AlAsr", "#TimeIsGold"],
    110: ["#AnNasr", "#Victory"],
    93:  ["#AdDuha", "#Hope", "#NeverGiveUp"],
    94:  ["#AshSharh", "#Relief", "#Patience"],
}


def generate_caption(ayah: dict) -> str:
    """
    Build an Instagram caption for the given ayah.

    Args:
        ayah: dict with keys arabic_text, translation, surah_id, ayah_number

    Returns:
        Formatted caption string.
    """
    arabic    = ayah.get("arabic_text", "")
    english   = ayah.get("translation", "")
    surah_id  = ayah.get("surah_id", 0)
    ayah_num  = ayah.get("ayah_number", 0)

    # Truncate long translation for readability
    if len(english) > 280:
        english = english[:277] + "…"

    # Pick hashtags
    surah_tags = SURAH_THEMES.get(surah_id, [])
    all_tags   = BASE_HASHTAGS[:6] + surah_tags[:3]
    hashtag_line = " ".join(all_tags)

    caption = (
        f"🌙 {arabic}\n\n"
        f'"{english}"\n\n'
        f"— Surah {surah_id}, Ayah {ayah_num} —\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"May Allah (ﷻ) bless you with this reminder 🤲\n\n"
        f"{hashtag_line}"
    )

    log.info(f"Caption generated ({len(caption)} chars) for {surah_id}:{ayah_num}")
    return caption
