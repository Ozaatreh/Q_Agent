"""
pipeline.py
───────────
Orchestrates Quran Reels pipeline.
"""

import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from config.settings import (
    MAX_WORDS_PER_AYAH,
    MAX_CHUNKS_PER_AYAH,
    MIN_SECONDS_PER_CHUNK,
)
from modules.logger import get_logger
from modules.ayah_picker import pick_ayahs, mark_published
from modules.audio_fetcher import fetch_audio_for_ayahs
from modules.video_generator import generate_video_for_ayahs, get_cinematic_chunks_for_text
from modules.caption_generator import generate_caption_for_ayahs
from modules.instagram_publisher import publish_reel
from modules.cloudinary_uploader import upload_video

log = get_logger("pipeline")


def _ayahs_are_valid(ayahs: list[dict], duration: float) -> bool:
    total_words = 0
    total_chunks = 0

    for ayah in ayahs:
        text = ayah["arabic_text"].strip()
        words = len(text.split())
        chunks = len(get_cinematic_chunks_for_text(text))

        total_words += words
        total_chunks += chunks

        if chunks > MAX_CHUNKS_PER_AYAH:
            log.info("Skipping %s — too many chunks (%s)", ayah["key"], chunks)
            return False

    if total_words > (MAX_WORDS_PER_AYAH * max(1, len(ayahs))):
        log.info("Skipping sequence — too many words (%s)", total_words)
        return False

    seconds_per_chunk = duration / max(total_chunks, 1)
    if seconds_per_chunk < MIN_SECONDS_PER_CHUNK:
        log.info("Skipping sequence — too fast to read (%.2fs/chunk)", seconds_per_chunk)
        return False

    return True


def _pick_valid_ayahs(max_attempts: int = 10):
    for attempt in range(1, max_attempts + 1):
        log.info("[1/7] Selecting ayah sequence… attempt %s/%s", attempt, max_attempts)
        ayahs = pick_ayahs()
        if not ayahs:
            continue

        log.info("[2/7] Fetching recitation audio…")
        audio_result = fetch_audio_for_ayahs(ayahs)
        if not audio_result:
            continue

        audio_path, duration, reciter_label = audio_result

        log.info("[3/7] Validating readability…")
        if not _ayahs_are_valid(ayahs, duration):
            continue

        return ayahs, audio_path, duration, reciter_label

    return None, None, None, None


def run_pipeline() -> bool:
    try:
        ayahs, audio_path, duration, reciter_label = _pick_valid_ayahs(max_attempts=10)
        if not ayahs:
            log.error("Failed to find suitable ayah sequence")
            return False

        log.info("[4/7] Generating video…")
        video_path = generate_video_for_ayahs(ayahs, audio_path, duration)
        if not video_path:
            log.error("Failed to generate video")
            return False

        log.info("[5/7] Uploading video…")
        public_url = upload_video(video_path)
        if not public_url:
            return False

        log.info("[6/7] Generating caption…")
        caption = generate_caption_for_ayahs(ayahs, reciter_label=reciter_label)

        log.info("[7/7] Publishing to Instagram…")
        media_id = publish_reel(video_path, caption, public_url)
        if not media_id:
            return False

        mark_published([a["key"] for a in ayahs])
        return True

    except Exception as e:
        log.error("Unexpected pipeline error: %s", e)
        log.debug(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
