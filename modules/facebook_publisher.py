"""
facebook_publisher.py
─────────────────────
Publishes a Reel to a Facebook Page via the Graph API.

Flow:
  1. Start a reel upload session on /{page_id}/video_reels
  2. Upload the MP4 bytes to the returned upload_url
  3. Finish/publish the reel on /{page_id}/video_reels

Requirements:
  • Facebook Page ID
  • Facebook Page access token
  • A user/Page token with permission to create content on the Page
"""

import time
from pathlib import Path
from typing import Optional

import requests

from config.settings import (
    FACEBOOK_PAGE_ID,
    FACEBOOK_PAGE_ACCESS_TOKEN,
    FACEBOOK_BASE_URL,
    MAX_RETRIES,
    RETRY_DELAY_SEC,
)
from modules.logger import get_logger

log = get_logger("facebook_publisher")


def _api_post(endpoint: str, data: dict) -> Optional[dict]:
    url = f"{FACEBOOK_BASE_URL}{endpoint}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(url, data=data, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            body = ""
            try:
                body = e.response.text[:1000]
            except Exception:
                pass
            log.warning(f"Facebook API POST attempt {attempt} HTTP error: {e} — {body}")
        except requests.RequestException as e:
            log.warning(f"Facebook API POST attempt {attempt} failed: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SEC)

    return None


def _start_reel_upload() -> Optional[dict]:
    """
    Step 1 — Start the Facebook Reel upload session.
    Returns dict containing at least upload_url and video_id on success.
    """
    data = {
        "upload_phase": "start",
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
    }

    result = _api_post(f"/{FACEBOOK_PAGE_ID}/video_reels", data)
    if result and result.get("upload_url") and result.get("video_id"):
        log.info(f"Facebook reel upload session started. Video ID: {result['video_id']}")
        return result

    log.error(f"Failed to start Facebook reel upload session: {result}")
    return None


def _upload_video_bytes(upload_url: str, video_path: Path) -> bool:
    """
    Step 2 — Upload the MP4 bytes to Meta using the upload_url returned by start phase.
    """
    try:
        with open(video_path, "rb") as f:
            files = {
                "file": (video_path.name, f, "video/mp4")
            }
            r = requests.post(upload_url, files=files, timeout=300)
            r.raise_for_status()

        log.info("Facebook reel video bytes uploaded successfully")
        return True

    except requests.HTTPError as e:
        body = ""
        try:
            body = e.response.text[:1000]
        except Exception:
            pass
        log.error(f"Facebook reel byte upload failed: {e} — {body}")
        return False
    except requests.RequestException as e:
        log.error(f"Facebook reel byte upload failed: {e}")
        return False


def _finish_reel_publish(video_id: str, caption: str) -> Optional[str]:
    """
    Step 3 — Finish and publish the Facebook Reel.
    """
    data = {
        "upload_phase": "finish",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "description": caption,
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN,
    }

    result = _api_post(f"/{FACEBOOK_PAGE_ID}/video_reels", data)
    if result and result.get("success"):
        post_id = result.get("post_id") or video_id
        log.info(f"Facebook Reel published successfully. Post ID: {post_id}")
        return post_id

    log.error(f"Facebook reel publish failed: {result}")
    return None


def publish_facebook_reel(video_path: Path, caption: str) -> Optional[str]:
    """
    Full Facebook Reel pipeline:
      start -> upload bytes -> finish/publish

    Returns post_id (or video_id fallback) on success, or None on failure.
    """
    if not FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ACCESS_TOKEN:
        log.warning(
            "Facebook credentials not configured. "
            "Set FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN env vars. "
            "Skipping Facebook publish."
        )
        return "DRY_RUN"

    if not video_path.exists():
        log.error(f"Facebook publish failed: video file not found: {video_path}")
        return None

    log.info(f"Publishing Facebook Reel: {video_path.name}")

    start_data = _start_reel_upload()
    if not start_data:
        return None

    upload_url = start_data["upload_url"]
    video_id = start_data["video_id"]

    if not _upload_video_bytes(upload_url, video_path):
        return None

    return _finish_reel_publish(video_id, caption)