"""
pipeline.py
───────────
Orchestrates the full Quran Reels pipeline:

  1. Pick an ayah
  2. Fetch recitation audio
  3. Validate ayah suitability
  4. Generate video
  5. Upload video
  6. Generate caption
  7. Publish to Instagram
  8. Mark as published
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
from modules.ayah_picker import pick_ayah, mark_published
from modules.audio_fetcher import fetch_audio
from modules.video_generator import generate_video, get_cinematic_chunks_for_text
from modules.caption_generator import generate_caption
from modules.instagram_publisher import publish_reel
from modules.cloudinary_uploader import upload_video
from modules.facebook_publisher import publish_facebook_reel

log = get_logger("pipeline")


def _ayah_is_valid(ayah: dict, duration: float) -> bool:
    text = ayah["arabic_text"].strip()
    word_count = len(text.split())

    chunks = get_cinematic_chunks_for_text(text)
    chunk_count = len(chunks)

    if word_count > MAX_WORDS_PER_AYAH:
        log.info(
            f"Skipping ayah {ayah['key']} — too many words "
            f"({word_count} > {MAX_WORDS_PER_AYAH})"
        )
        return False

    if chunk_count > MAX_CHUNKS_PER_AYAH:
        log.info(
            f"Skipping ayah {ayah['key']} — too many chunks "
            f"({chunk_count} > {MAX_CHUNKS_PER_AYAH})"
        )
        return False

    seconds_per_chunk = duration / max(chunk_count, 1)
    if seconds_per_chunk < MIN_SECONDS_PER_CHUNK:
        log.info(
            f"Skipping ayah {ayah['key']} — too fast to read "
            f"({seconds_per_chunk:.2f}s/chunk < {MIN_SECONDS_PER_CHUNK:.2f}s)"
        )
        return False

    log.info(
        f"      ✓ Ayah validation passed "
        f"(words={word_count}, chunks={chunk_count}, "
        f"seconds/chunk={seconds_per_chunk:.2f})"
    )
    return True


def _pick_valid_ayah(max_attempts: int = 10):
    """
    Keep trying until a suitable ayah is found, or attempts run out.
    """
    for attempt in range(1, max_attempts + 1):
        log.info(f"[1/7] Selecting ayah… attempt {attempt}/{max_attempts}")
        ayah = pick_ayah()
        if not ayah:
            log.warning("Failed to select an ayah on this attempt.")
            continue

        log.info(f"      ✓ Candidate ayah {ayah['key']}: {ayah['arabic_text'][:60]}…")

        log.info("[2/7] Fetching recitation audio…")
        audio_result = fetch_audio(ayah)
        if not audio_result:
            log.warning("Failed to fetch audio for this ayah. Trying another one.")
            continue

        audio_path, duration, reciter_label = audio_result
        log.info(f"      ✓ Audio: {audio_path.name} ({duration:.1f}s) — {reciter_label}")

        log.info("[3/7] Validating ayah for reel readability…")
        if not _ayah_is_valid(ayah, duration):
            log.warning("Ayah is not suitable. Trying another one.")
            continue

        return ayah, audio_path, duration, reciter_label

    return None, None, None, None 


def run_pipeline() -> bool:
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  Quran Reels Agent — Pipeline Starting")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        ayah, audio_path, duration, reciter_label = _pick_valid_ayah(max_attempts=10)
        if not ayah:
            log.error("Failed to find a suitable ayah. Aborting pipeline.")
            return False

        # 4. Generate Video
        log.info("[4/7] Generating video…")
        video_path = generate_video(ayah, audio_path, duration)
        if not video_path:
            log.error("Failed to generate video. Aborting pipeline.")
            return False
        log.info(f"      ✓ Video: {video_path.name}")

        # 5. Upload Video
        log.info("[5/7] Uploading video…")
        public_url = upload_video(video_path)
        if not public_url:
            log.error("Failed to upload video. Aborting pipeline.")
            return False
        log.info(f"      ✓ Video uploaded: {public_url}")

        # 6. Generate Caption
        log.info("[6/7] Generating caption…")
        caption = generate_caption(ayah)
        caption += f"\n\n🎧 القارئ: {reciter_label}"

        # # 7. Publish to Instagram
        log.info("[7/7] Publishing to Instagram…")
        media_id = publish_reel(video_path, caption, public_url)
        if not media_id:
            log.error("Failed to publish Instagram Reel.")
            return False
        log.info(f"      ✓ Instagram published — Media ID: {media_id}")

        # Optional Facebook publish
        # fb_post_id = publish_facebook_reel(video_path, caption)
        # if not fb_post_id:
        #     log.error("Failed to publish Facebook Reel.")
        #     return False
        # log.info(f"      ✓ Facebook published — Post ID: {fb_post_id}")

        # 8. Mark as published
        mark_published(ayah["key"])
        log.info(f"      ✓ Marked as published: {ayah['key']}")

        log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log.info("  Pipeline completed successfully ✓")
        log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return True

    except Exception as e:
        log.error(f"Unexpected pipeline error: {e}")
        log.debug(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)