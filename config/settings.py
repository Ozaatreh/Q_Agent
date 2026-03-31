"""
Configuration settings for the Quran Reels Agent.
Copy this file and fill in your credentials.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
VIDEOS_DIR = OUTPUT_DIR / "videos"
AUDIO_DIR = OUTPUT_DIR / "audio"
LOGS_DIR = OUTPUT_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

for d in [VIDEOS_DIR, AUDIO_DIR, LOGS_DIR, ASSETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# INSTAGRAM GRAPH API
# ─────────────────────────────────────────────
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN_HERE")
INSTAGRAM_BUSINESS_ID   = os.getenv("INSTAGRAM_BUSINESS_ID",  "YOUR_BUSINESS_ACCOUNT_ID")
META_APP_ID = os.getenv("META_APP_ID", "")
INSTAGRAM_API_VERSION   = "v19.0"
INSTAGRAM_BASE_URL      = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}"
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "957146090198306")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "EAANbkHeAU9IBRHbd0yeIDS7FwWomOeEXZBFaAhjBKAU9UhtQjkyTzWqSBkUvyAp8DtJ2sx5xrSZBeneOKYJJ9kXxV5u6gK3qreLADy7m3vTjxOTqOZAUAbJSWPX3POtKA08wZAugv7qxF7jihTlTlSECF49aF8fxrfmZCALjegYH3av4Ao42fFpKZBBlqDqC7z")
FACEBOOK_API_VERSION = "v19.0"
FACEBOOK_BASE_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "dxzvorbh7")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "578295819533355")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "yKmupxCy5huc7z5aGVysES0dTdE")
# ─────────────────────────────────────────────
# QURAN API  (quran.com v4)
# ─────────────────────────────────────────────
QURAN_API_BASE          = "https://api.quran.com/api/v4"
QURAN_CDN_BASE          = "https://verses.quran.com"

# Reciter configuration.
# We keep Mishary as the primary stable reciter in production.
RECITER_KEYS = ["mishary"]

RECITERS = {
    "mishary": {
        "label": "مشاري العفاسي",
        "folder": "Alafasy",
    },
    "maher": {
        "label": "ماهر المعيقلي",
        "folder": "MaherAlMuaiqly",
    },
    "minshawi": {
        "label": "المنشاوي",
        "folder": "Minshawy",
    },
    "abdul_basit": {
        "label": "عبد الباسط",
        "folder": "AbdulSamad",
    },
}

EVERYAYAH_BASE_URL = "https://everyayah.com/data"

# Short surahs ideal for Reels (15-30 s).  Expand as desired.
# SHORT_SURAH_IDS = [
#     1,   # Al-Fatiha
#     112, # Al-Ikhlas
#     113, # Al-Falaq
#     114, # An-Nas
#     108, # Al-Kawthar
#     103, # Al-Asr
#     110, # An-Nasr
#     111, # Al-Masad (skipped if long)
#     94,  # Ash-Sharh
#     93,  # Ad-Duha (first 5 ayas)
# ]
SHORT_SURAH_IDS = [
    1,
    78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90,
    91, 92, 93, 94, 95, 96, 97, 98, 99, 100,
    101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114
]

MAX_WORDS_PER_AYAH = 18
MAX_CHUNKS_PER_AYAH = 3
MIN_SECONDS_PER_CHUNK = 1.8

# ─────────────────────────────────────────────
# CONTENT ENGINE SETTINGS
# ─────────────────────────────────────────────
ENABLE_MULTI_AYAH = True
MAX_AYAHS_PER_VIDEO = 5
MIN_AYAHS_PER_VIDEO = 2

# Options: "cinematic" (fade between ayahs) / "stacked" (top-to-bottom)
MULTI_AYAH_LAYOUT = "cinematic"

ENABLE_TAFSIR = True
# ─────────────────────────────────────────────
# VIDEO SETTINGS
# ─────────────────────────────────────────────
VIDEO_WIDTH      = 1080
VIDEO_HEIGHT     = 1920   # 9:16 vertical
VIDEO_FPS        = 30
VIDEO_MIN_SEC    = 15
VIDEO_MAX_SEC    = 30
FADE_DURATION    = 1.0    # seconds for fade in/out

# Background color fallback (deep night blue) when no background video
BG_COLOR         = (10, 15, 40)

# Arabic font — Amiri is embedded in assets/; fallback to system
FONT_NAME        = "Amiri"          # will resolve to assets/Amiri-Regular.ttf
FONT_SIZE        = 72               # px — will auto-scale

# ─────────────────────────────────────────────
# SCHEDULING  (times in 24h, server local time)
# ─────────────────────────────────────────────
PUBLISH_TIMES = ["07:00", "10:00", "13:00", "16:00", "20:00"]

# ─────────────────────────────────────────────
# RETRY / LOGGING
# ─────────────────────────────────────────────
MAX_RETRIES      = 3
RETRY_DELAY_SEC  = 10
LOG_LEVEL        = "INFO"
PUBLISHED_LOG    = OUTPUT_DIR / "published_ayahs.json"
