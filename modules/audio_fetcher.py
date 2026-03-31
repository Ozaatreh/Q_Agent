"""
audio_fetcher.py
────────────────
Fetches Quran ayah audio from Quran CDN (verses.quran.com)

Features:
- Multiple reciters
- Automatic fallback to Mishary (Alafasy)
- Duration detection via ffprobe
- Local caching

Returns:
    (audio_path: Path, duration_sec: float, reciter_label: str) | None
"""

import random
import subprocess
from pathlib import Path

import requests

from config.settings import AUDIO_DIR
from modules.logger import get_logger

log = get_logger("audio_fetcher")


# ✅ Supported stable reciters on Quran CDN
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

RECITER_KEYS = list(RECITERS.keys())


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _pick_reciter():
    key = random.choice(RECITER_KEYS)
    return key, RECITERS[key]


def _download_file(url: str, out_path: Path) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=60)
        if r.status_code != 200:
            log.warning(f"Download failed [{r.status_code}] for URL: {url}")
            return False

        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)

        return True

    except Exception as e:
        log.warning(f"Download error for {url}: {e}")
        return False


def _probe_duration(audio_path: Path) -> float | None:
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if res.returncode != 0:
            return None

        return float(res.stdout.strip())

    except Exception as e:
        log.warning(f"Could not probe duration: {e}")
        return None


def _quran_cdn_ayah_url(folder: str, surah_id: int, ayah_number: int) -> str:
    ayah_code = f"{surah_id:03}{ayah_number:03}"
    return f"https://verses.quran.com/{folder}/mp3/{ayah_code}.mp3"


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def fetch_audio(ayah: dict):
    """
    Fetch ayah audio from Quran CDN using random reciter.

    Returns:
        (audio_path, duration, reciter_label) or None
    """

    surah_id = int(ayah["surah_id"])
    ayah_number = int(ayah["ayah_number"])

    safe_key = ayah["key"].replace(":", "_")

    # 🎯 Pick random reciter
    reciter_key, reciter = _pick_reciter()
    reciter_label = reciter["label"]
    folder = reciter["folder"]

    out_path = AUDIO_DIR / f"{safe_key}__{reciter_key}.mp3"

    # ✅ Use cache if exists
    if out_path.exists() and out_path.stat().st_size > 50_000:
        duration = _probe_duration(out_path)
        if duration:
            log.info(f"Reusing cached audio for {reciter_label}: {out_path.name}")
            return out_path, duration, reciter_label

    # 🎧 Primary attempt
    audio_url = _quran_cdn_ayah_url(folder, surah_id, ayah_number)
    log.info(f"Downloading audio for {reciter_label}...")

    ok = _download_file(audio_url, out_path)

    # 🔁 Fallback to Mishary (always works)
    if not ok:
        log.warning(f"{reciter_label} failed — fallback to مشاري العفاسي")

        fallback_folder = "Alafasy"
        reciter_label = "مشاري العفاسي"

        out_path = AUDIO_DIR / f"{safe_key}__fallback.mp3"
        audio_url = _quran_cdn_ayah_url(fallback_folder, surah_id, ayah_number)

        ok = _download_file(audio_url, out_path)

        if not ok:
            log.error("Fallback also failed — giving up.")
            return None

    # 🎯 Get duration
    duration = _probe_duration(out_path)

    if not duration:
        log.error("Audio downloaded but duration could not be determined.")
        return None

    return out_path, duration, reciter_label