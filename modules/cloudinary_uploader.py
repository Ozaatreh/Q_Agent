from pathlib import Path
import cloudinary
import cloudinary.uploader
from modules.logger import get_logger
from config.settings import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
)

log = get_logger("cloudinary_uploader")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)

def upload_video(video_path: Path) -> str | None:
    try:
        result = cloudinary.uploader.upload_large(
            str(video_path),
            resource_type="video",
            folder="quran_reels_agent",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        url = result.get("secure_url")
        if url:
            log.info(f"Uploaded video to Cloudinary: {url}")
            return url
        log.error(f"Cloudinary upload succeeded but no secure_url returned: {result}")
        return None
    except Exception as e:
        log.error(f"Cloudinary upload failed: {e}")
        return None