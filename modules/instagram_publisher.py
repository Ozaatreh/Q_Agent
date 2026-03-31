"""
instagram_publisher.py
──────────────────────
Publishes a video Reel to Instagram via the Graph API.

Flow:
  1. Upload video to a publicly accessible location (or use a public URL).
     Since we're running locally, we use the Graph API's resumable upload.
  2. Create a container (media object) for the Reel.
  3. Poll until processing is complete.
  4. Publish the container.

Requirements:
  • Instagram Business or Creator account
  • Facebook App with instagram_basic + instagram_content_publish permissions
  • Access token with the above permissions

NOTE: The Graph API requires the video to be accessible via a public URL.
      This module uploads the video using the resumable upload endpoint.
      For production, host the video on S3 / Cloudflare R2 / similar.
"""

import time
from pathlib import Path
from typing import Optional

import requests

from config.settings import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_BUSINESS_ID,
    INSTAGRAM_BASE_URL,
    META_APP_ID,
    MAX_RETRIES,
    RETRY_DELAY_SEC,
)
from modules.logger import get_logger

log = get_logger("instagram_publisher")

PUBLISH_POLL_INTERVAL = 10   # seconds between status checks
PUBLISH_POLL_MAX      = 30   # max poll attempts (~5 minutes)


# ── internal helpers ─────────────────────────────────────────────────────────

def _api_post(endpoint: str, data: dict, files=None) -> Optional[dict]:
    """POST to Graph API with retry logic."""
    url = f"{INSTAGRAM_BASE_URL}{endpoint}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if files:
                r = requests.post(url, data=data, files=files, timeout=120)
            else:
                r = requests.post(url, data=data, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            body = ""
            try:
                body = e.response.text[:1000]
            except Exception:
                pass
            log.warning(f"API POST attempt {attempt} HTTP error: {e} — {body}")
        except requests.RequestException as e:
            log.warning(f"API POST attempt {attempt} failed: {e}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SEC)
    return None


def _api_get(endpoint: str, params: dict = None) -> Optional[dict]:
    """GET from Graph API."""
    url = f"{INSTAGRAM_BASE_URL}{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning(f"API GET failed: {e}")
        return None


def _create_reel_container(video_path: Path, caption: str, public_url: str | None = None) -> Optional[str]:
    import os

    final_url = public_url or os.getenv("VIDEO_PUBLIC_URL")
    if not final_url:
        log.error("No public video URL available.")
        return None

    data = {
        "media_type": "REELS",
        "video_url": final_url,
        "caption": caption,
        "share_to_feed": "true",
        "thumb_offset": "1000",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }

    result = _api_post(f"/{INSTAGRAM_BUSINESS_ID}/media", data)
    if result and "id" in result:
        log.info(f"Container created: {result['id']}")
        return result["id"]

    log.error(f"Container creation failed: {result}")
    return None

def _wait_for_processing(container_id: str) -> bool:
    """
    Step 2 — Poll until IG finishes processing the video.
    Returns True if processing succeeded.
    """
    params = {
        "fields":       "status_code,status",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    for attempt in range(PUBLISH_POLL_MAX):
        time.sleep(PUBLISH_POLL_INTERVAL)
        data = _api_get(f"/{container_id}", params)
        if not data:
            log.warning(f"Poll attempt {attempt + 1}: no response")
            continue

        status = data.get("status_code", "UNKNOWN")
        log.info(f"Container status (attempt {attempt + 1}): {status}")

        if status == "FINISHED":
            return True
        if status in ("ERROR", "EXPIRED"):
            log.error(f"Container processing failed: {data.get('status', '')}")
            return False

    log.error("Container never reached FINISHED status")
    return False


def _publish_container(container_id: str) -> Optional[str]:
    """
    Step 3 — Publish the media container.
    Returns the new media ID on success.
    """
    data = {
        "creation_id":  container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    result = _api_post(f"/{INSTAGRAM_BUSINESS_ID}/media_publish", data)
    if result and "id" in result:
        log.info(f"Published! Media ID: {result['id']}")
        return result["id"]
    log.error(f"Publish failed: {result}")
    return None


# ── public API ────────────────────────────────────────────────────────────────

def publish_reel(video_path: Path, caption: str, video_url: str | None = None) -> Optional[str]:
    """
    Full publish pipeline: upload → wait → publish.

    Returns the Instagram media ID on success, or None on failure.
    """
    if not INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_ACCESS_TOKEN.startswith("YOUR_"):
        log.warning(
            "Instagram credentials not configured. "
            "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID env vars. "
            "Skipping publish (dry-run mode)."
        )
        return "DRY_RUN"

    log.info(f"Publishing Reel: {video_path.name}")

    # 1. Create container
    container_id = _create_reel_container(video_path, caption, video_url)
    if not container_id:
        return None

    # 2. Wait for processing
    if not _wait_for_processing(container_id):
        return None

    # 3. Publish
    media_id = _publish_container(container_id)
    return media_id
