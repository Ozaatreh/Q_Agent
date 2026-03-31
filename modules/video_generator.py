"""
video_generator.py
──────────────────
Cinematic Quran reel generator with:
- Multi-ayah support (2-5 sequential ayahs)
- Long ayah chunking with dynamic audio-synced durations
- Arabic shaping + RTL-safe wrapping with diacritics preserved
- 9:16 output with fade transitions and subtle zoom
"""

import math
import random
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from config.settings import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    ASSETS_DIR,
    VIDEOS_DIR,
    FONT_SIZE,
    MULTI_AYAH_LAYOUT,
    MAX_CHUNKS_PER_AYAH,
    MIN_SECONDS_PER_CHUNK,
)
from modules.logger import get_logger

log = get_logger("video_generator")

W, H = VIDEO_WIDTH, VIDEO_HEIGHT


SURAH_NAMES_AR = {
    1: "الفاتحة", 2: "البقرة", 3: "آل عمران", 4: "النساء", 5: "المائدة",
    6: "الأنعام", 7: "الأعراف", 8: "الأنفال", 9: "التوبة", 10: "يونس",
    11: "هود", 12: "يوسف", 13: "الرعد", 14: "إبراهيم", 15: "الحجر",
    16: "النحل", 17: "الإسراء", 18: "الكهف", 19: "مريم", 20: "طه",
    21: "الأنبياء", 22: "الحج", 23: "المؤمنون", 24: "النور", 25: "الفرقان",
    26: "الشعراء", 27: "النمل", 28: "القصص", 29: "العنكبوت", 30: "الروم",
    31: "لقمان", 32: "السجدة", 33: "الأحزاب", 34: "سبأ", 35: "فاطر",
    36: "يس", 37: "الصافات", 38: "ص", 39: "الزمر", 40: "غافر",
    41: "فصلت", 42: "الشورى", 43: "الزخرف", 44: "الدخان", 45: "الجاثية",
    46: "الأحقاف", 47: "محمد", 48: "الفتح", 49: "الحجرات", 50: "ق",
    51: "الذاريات", 52: "الطور", 53: "النجم", 54: "القمر", 55: "الرحمن",
    56: "الواقعة", 57: "الحديد", 58: "المجادلة", 59: "الحشر", 60: "الممتحنة",
    61: "الصف", 62: "الجمعة", 63: "المنافقون", 64: "التغابن", 65: "الطلاق",
    66: "التحريم", 67: "الملك", 68: "القلم", 69: "الحاقة", 70: "المعارج",
    71: "نوح", 72: "الجن", 73: "المزمل", 74: "المدثر", 75: "القيامة",
    76: "الإنسان", 77: "المرسلات", 78: "النبأ", 79: "النازعات", 80: "عبس",
    81: "التكوير", 82: "الإنفطار", 83: "المطففين", 84: "الإنشقاق", 85: "البروج",
    86: "الطارق", 87: "الأعلى", 88: "الغاشية", 89: "الفجر", 90: "البلد",
    91: "الشمس", 92: "الليل", 93: "الضحى", 94: "الشرح", 95: "التين",
    96: "العلق", 97: "القدر", 98: "البينة", 99: "الزلزلة", 100: "العاديات",
    101: "القارعة", 102: "التكاثر", 103: "العصر", 104: "الهمزة", 105: "الفيل",
    106: "قريش", 107: "الماعون", 108: "الكوثر", 109: "الكافرون", 110: "النصر",
    111: "المسد", 112: "الإخلاص", 113: "الفلق", 114: "الناس",
}


def _find_fonts() -> tuple[Optional[Path], Optional[Path]]:
    primary_candidates = [ASSETS_DIR / "Amiri-Regular.ttf", ASSETS_DIR / "NotoNaskhArabic-Regular.ttf"]
    fallback_candidates = [ASSETS_DIR / "NotoNaskhArabic-Regular.ttf", ASSETS_DIR / "Amiri-Regular.ttf"]
    primary = next((c for c in primary_candidates if c.exists()), None)
    fallback = next((c for c in fallback_candidates if c.exists()), None)
    return primary, fallback


def _shape_arabic(text: str) -> str:
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _normalize_text(text: str) -> str:
    # Keep harakat; only normalize spacing.
    return re.sub(r"\s+", " ", (text or "").strip())


def _split_by_meaning(text: str) -> list[str]:
    separators = r"([،؛,:.!؟])"
    parts = re.split(separators, text)
    chunks: list[str] = []
    current = ""
    for part in parts:
        token = part.strip()
        if not token:
            continue
        if re.fullmatch(separators, token):
            current = f"{current}{token}".strip()
            if current:
                chunks.append(current)
            current = ""
            continue

        if not current:
            current = token
        elif len((current + " " + token).split()) <= 8:
            current = f"{current} {token}"
        else:
            chunks.append(current)
            current = token

    if current:
        chunks.append(current)
    return chunks or [text]


def _pick_background_image() -> Optional[Path]:
    bg_dir = ASSETS_DIR / "backgrounds"
    if not bg_dir.exists():
        return None
    candidates = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        candidates.extend(bg_dir.glob(ext))
    return random.choice(candidates) if candidates else None


def _prepare_background(bg_path: Path):
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(bg_path).convert("RGBA")
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = W / H

    if src_ratio > target_ratio:
        nw = int(src_h * target_ratio)
        left = (src_w - nw) // 2
        img = img.crop((left, 0, left + nw, src_h))
    else:
        nh = int(src_w / target_ratio)
        top = (src_h - nh) // 2
        img = img.crop((0, top, src_w, top + nh))

    img = img.resize((W, H), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.35))
    img = ImageEnhance.Brightness(img).enhance(0.9)
    return img


def _wrap_text_raw(text: str, font, draw, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        bb = draw.textbbox((0, 0), candidate, font=font)
        if (bb[2] - bb[0]) <= max_width:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _fit_font_and_lines(raw_text: str, font_path: Optional[Path], max_w: int, max_h: int, draw, start_size: int = FONT_SIZE):
    from PIL import ImageFont

    size = start_size
    while size >= 38:
        font = ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default()
        lines = _wrap_text_raw(raw_text, font, draw, max_w)
        bb = draw.textbbox((0, 0), "بِسْمِ اللَّهِ", font=font)
        line_h = (bb[3] - bb[1]) + max(18, int(size * 0.22))
        if line_h * len(lines) <= max_h and len(lines) <= 5:
            return font, lines, line_h
        size -= 4

    font = ImageFont.truetype(str(font_path), 38) if font_path else ImageFont.load_default()
    lines = _wrap_text_raw(raw_text, font, draw, max_w)
    bb = draw.textbbox((0, 0), "بِسْمِ اللَّهِ", font=font)
    return font, lines, (bb[3] - bb[1]) + 16


def _render_frame(bg, lines: list[str], ref_text: str, font_path: Optional[Path], fallback_font_path: Optional[Path]) -> Optional[Path]:
    from PIL import ImageDraw, ImageFont

    frame = bg.copy()
    draw = ImageDraw.Draw(frame, "RGBA")

    font, fitted_lines, line_h = _fit_font_and_lines(" ".join(lines), font_path, int(W * 0.78), int(H * 0.52), draw)
    fallback_font = ImageFont.truetype(str(fallback_font_path), getattr(font, "size", 42)) if fallback_font_path else font

    shaped_lines = [_shape_arabic(line) for line in fitted_lines]
    total_h = line_h * len(shaped_lines)
    y = int(H * 0.44 - total_h / 2)

    for line in shaped_lines:
        bb = draw.textbbox((0, 0), line, font=font)
        x = (W - (bb[2] - bb[0])) // 2
        draw.text((x + 2, y + 2), line, font=fallback_font, fill=(0, 0, 0, 120))
        draw.text((x, y), line, font=font, fill=(245, 242, 235, 255))
        y += line_h

    ref_font = ImageFont.truetype(str(font_path), 34) if font_path else ImageFont.load_default()
    shaped_ref = _shape_arabic(ref_text)
    rbb = draw.textbbox((0, 0), shaped_ref, font=ref_font)
    rx = (W - (rbb[2] - rbb[0])) // 2
    draw.text((rx + 1, int(H * 0.82) + 1), shaped_ref, font=ref_font, fill=(0, 0, 0, 100))
    draw.text((rx, int(H * 0.82)), shaped_ref, font=ref_font, fill=(230, 225, 215, 230))

    out = Path(tempfile.mktemp(suffix=".png"))
    frame.convert("RGB").save(str(out), "PNG")
    return out


def _build_ayah_chunks(raw_text: str) -> list[str]:
    base_chunks = _split_by_meaning(_normalize_text(raw_text))
    if len(base_chunks) <= MAX_CHUNKS_PER_AYAH:
        return base_chunks

    # fallback: merge excess chunks to stay within configured cap
    merged: list[str] = []
    for chunk in base_chunks:
        if len(merged) < MAX_CHUNKS_PER_AYAH:
            merged.append(chunk)
        else:
            merged[-1] = f"{merged[-1]} {chunk}".strip()
    return merged


def get_cinematic_chunks_for_text(raw_text: str) -> list[str]:
    return _build_ayah_chunks(raw_text)


def _timeline_for_ayahs(ayahs: list[dict], duration: float) -> list[tuple[str, float, dict]]:
    words_total = sum(max(1, len(a.get("arabic_text", "").split())) for a in ayahs)
    sequence: list[tuple[str, float, dict]] = []

    for ayah in ayahs:
        ayah_chunks = _build_ayah_chunks(ayah.get("arabic_text", ""))
        ayah_words = max(1, len(ayah.get("arabic_text", "").split()))
        ayah_duration = duration * (ayah_words / words_total)

        chunk_words = [max(1, len(c.split())) for c in ayah_chunks]
        sum_chunk_words = sum(chunk_words)

        for chunk, c_words in zip(ayah_chunks, chunk_words):
            c_duration = max(MIN_SECONDS_PER_CHUNK, ayah_duration * (c_words / sum_chunk_words))
            sequence.append((chunk, c_duration, ayah))

    # Re-normalize durations to exact audio duration.
    total = sum(seg[1] for seg in sequence) or 1.0
    scale = duration / total
    return [(text, max(0.6, d * scale), meta) for text, d, meta in sequence]


def _encode_video(sequence: list[tuple[Path, float]], audio: Path, out: Path) -> bool:
    inputs = []
    filters = []

    for idx, (frame, seg_dur) in enumerate(sequence):
        fade = min(0.5, max(0.2, seg_dur * 0.2))
        inputs += ["-loop", "1", "-t", f"{seg_dur:.3f}", "-i", str(frame)]
        filters.append(
            f"[{idx}:v]fps={VIDEO_FPS},scale={W}:{H},"
            f"zoompan=z='min(zoom+0.0007,1.07)':d=1:s={W}x{H},"
            f"fade=t=in:st=0:d={fade:.2f},"
            f"fade=t=out:st={max(0, seg_dur-fade):.2f}:d={fade:.2f}[v{idx}]"
        )

    concat_in = "".join(f"[v{i}]" for i in range(len(sequence)))
    filter_complex = ";".join(filters) + f";{concat_in}concat=n={len(sequence)}:v=1:a=0[outv]"

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-i", str(audio),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{len(sequence)}:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(VIDEO_FPS),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart",
        str(out),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if res.returncode != 0:
        log.error("FFmpeg error: %s", res.stderr[-1500:])
        return False
    return True


def _stacked_frame_lines(ayahs: list[dict]) -> list[str]:
    lines: list[str] = []
    for ayah in ayahs:
        lines.append(ayah.get("arabic_text", ""))
    return lines


def generate_video(ayah: dict, audio_path: Path, duration: float) -> Optional[Path]:
    return generate_video_for_ayahs([ayah], audio_path, duration)


def generate_video_for_ayahs(ayahs: list[dict], audio_path: Path, duration: float) -> Optional[Path]:
    if not ayahs:
        return None

    seq_key = "_".join(a["key"].replace(":", "_") for a in ayahs)
    out_path = VIDEOS_DIR / f"reel_{seq_key}.mp4"

    if out_path.exists() and out_path.stat().st_size > 50_000:
        return out_path

    font_path, fallback_font_path = _find_fonts()
    bg_path = _pick_background_image()
    if not bg_path:
        log.error("No background images found")
        return None

    bg = _prepare_background(bg_path)
    surah_name = ayahs[0].get("surah_name_ar") or SURAH_NAMES_AR.get(int(ayahs[0]["surah_id"]), "")
    ref_text = f"سورة {surah_name} • الآيات {ayahs[0]['ayah_number']}-{ayahs[-1]['ayah_number']}"

    rendered: list[Path] = []
    timed_frames: list[tuple[Path, float]] = []

    try:
        if MULTI_AYAH_LAYOUT == "stacked" and len(ayahs) > 1:
            frame = _render_frame(bg, _stacked_frame_lines(ayahs), ref_text, font_path, fallback_font_path)
            if not frame:
                return None
            rendered.append(frame)
            timed_frames = [(frame, duration)]
        else:
            for text, seg_dur, meta in _timeline_for_ayahs(ayahs, duration):
                ref = f"سورة {meta.get('surah_name_ar') or surah_name} • آية {meta['ayah_number']}"
                frame = _render_frame(bg, [text], ref, font_path, fallback_font_path)
                if not frame:
                    continue
                rendered.append(frame)
                timed_frames.append((frame, seg_dur))

        if not timed_frames:
            return None

        return out_path if _encode_video(timed_frames, audio_path, out_path) else None
    finally:
        for f in rendered:
            f.unlink(missing_ok=True)
