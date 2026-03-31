"""
audio_fetcher.py
────────────────
Audio retrieval + concatenation for one or multiple ayahs.
"""

import subprocess
from pathlib import Path

import requests

from config.settings import AUDIO_DIR, RECITERS, RECITER_KEYS
from modules.logger import get_logger

log = get_logger("audio_fetcher")


def _download_file(url: str, out_path: Path) -> bool:
    try:
        res = requests.get(url, stream=True, timeout=60)
        if res.status_code != 200:
            log.warning("Download failed [%s] for URL: %s", res.status_code, url)
            return False

        with out_path.open("wb") as handle:
            for chunk in res.iter_content(chunk_size=1024 * 64):
                if chunk:
                    handle.write(chunk)
        return True
    except Exception as exc:
        log.warning("Download error for %s: %s", url, exc)
        return False


def _probe_duration(audio_path: Path) -> float | None:
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if res.returncode != 0:
            return None
        return float(res.stdout.strip())
    except Exception:
        return None


def _quran_cdn_ayah_url(folder: str, surah_id: int, ayah_number: int) -> str:
    ayah_code = f"{surah_id:03}{ayah_number:03}"
    return f"https://verses.quran.com/{folder}/mp3/{ayah_code}.mp3"


def _stable_reciter() -> tuple[str, dict]:
    key = RECITER_KEYS[0] if RECITER_KEYS else "mishary"
    return key, RECITERS.get(key, RECITERS["mishary"])


def fetch_audio(ayah: dict):
    """Backward-compatible single ayah fetch."""
    result = fetch_audio_for_ayahs([ayah])
    if not result:
        return None
    return result


def _fetch_single_ayah_audio(ayah: dict, reciter_key: str, reciter: dict):
    surah_id = int(ayah["surah_id"])
    ayah_number = int(ayah["ayah_number"])
    safe_key = ayah["key"].replace(":", "_")

    out_path = AUDIO_DIR / f"{safe_key}__{reciter_key}.mp3"
    if out_path.exists() and out_path.stat().st_size > 50_000:
        duration = _probe_duration(out_path)
        if duration:
            return out_path, duration

    audio_url = _quran_cdn_ayah_url(reciter["folder"], surah_id, ayah_number)
    if not _download_file(audio_url, out_path):
        return None

    duration = _probe_duration(out_path)
    if not duration:
        return None
    return out_path, duration


def _concat_audio(parts: list[Path], output_path: Path) -> bool:
    concat_file = output_path.with_suffix(".txt")
    concat_file.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts), encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:a", "aac", "-b:a", "128k",
        "-ar", "44100",
        str(output_path),
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            log.error("Audio concat failed: %s", res.stderr[-1000:])
            return False
        return True
    finally:
        concat_file.unlink(missing_ok=True)


def fetch_audio_for_ayahs(ayahs: list[dict]):
    """
    Fetch and optionally concatenate ayah-level audio in sequence.

    Returns:
        (audio_path, total_duration_sec, reciter_label) or None
    """
    if not ayahs:
        return None

    reciter_key, reciter = _stable_reciter()
    reciter_label = reciter["label"]

    parts: list[Path] = []
    total_duration = 0.0

    for ayah in ayahs:
        result = _fetch_single_ayah_audio(ayah, reciter_key, reciter)
        if not result:
            if reciter_key != "mishary":
                log.warning("Primary reciter failed. Retrying with Mishary.")
                reciter_key, reciter = "mishary", RECITERS["mishary"]
                reciter_label = reciter["label"]
                result = _fetch_single_ayah_audio(ayah, reciter_key, reciter)
        if not result:
            log.error("Failed to fetch ayah audio for %s", ayah.get("key"))
            return None

        part_path, duration = result
        parts.append(part_path)
        total_duration += duration

    if len(parts) == 1:
        return parts[0], total_duration, reciter_label

    seq_key = "_".join(a["key"].replace(":", "_") for a in ayahs)
    out_path = AUDIO_DIR / f"seq_{seq_key}__{reciter_key}.m4a"

    if out_path.exists() and out_path.stat().st_size > 50_000:
        duration = _probe_duration(out_path)
        if duration:
            return out_path, duration, reciter_label

    if not _concat_audio(parts, out_path):
        return None

    duration = _probe_duration(out_path)
    if not duration:
        return None

    return out_path, duration, reciter_label
