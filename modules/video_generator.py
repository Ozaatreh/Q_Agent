"""
video_generator.py
──────────────────
Cinematic Quran Reel generator:

  • Background image from assets/backgrounds/
  • Long ayah split into cinematic chunks by actual visual fit
  • One chunk shown at a time with fade in/out
  • Arabic wrapping BEFORE shaping (correct RTL order)
  • Better line balancing for Arabic top-to-bottom reading
  • Amiri as primary font, Noto Naskh as fallback
  • Surah name in Arabic
  • Static background, no zoom
  • Audio track
"""

import math
import random
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from modules.logger import get_logger
from config.settings import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    ASSETS_DIR, VIDEOS_DIR, FONT_SIZE,
)

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
    primary_candidates = [
        ASSETS_DIR / "Amiri-Regular.ttf",
        ASSETS_DIR / "NotoNaskhArabic-Regular.ttf",
    ]
    fallback_candidates = [
        ASSETS_DIR / "NotoNaskhArabic-Regular.ttf",
        ASSETS_DIR / "Amiri-Regular.ttf",
    ]

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


def _clean_quran_text(text: str) -> str:
    text = re.sub(r'[\u0610-\u061A]', '', text)
    text = re.sub(r'[\u06D6-\u06ED]', '', text)
    text = re.sub(r'[\u08D4-\u08E1]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _pick_background_image() -> Optional[Path]:
    bg_dir = ASSETS_DIR / "backgrounds"
    if not bg_dir.exists():
        return None

    candidates = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        candidates.extend(bg_dir.glob(ext))

    if not candidates:
        return None

    return random.choice(candidates)


def _prepare_background(bg_path: Path):
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

    img = Image.open(bg_path).convert("RGBA")

    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = W / H

    if src_ratio > target_ratio:
        new_h = src_h
        new_w = int(new_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_w = src_w
        new_h = int(new_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    img = img.resize((W, H), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
    img = ImageEnhance.Contrast(img).enhance(0.96)
    img = ImageEnhance.Brightness(img).enhance(0.95)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    for y in range(H):
        if y < int(H * 0.20):
            alpha = int(70 * (1 - y / (H * 0.20)))
        elif y > int(H * 0.78):
            alpha = int(80 * ((y - H * 0.78) / (H * 0.22)))
        else:
            alpha = 22
        od.line([(0, y), (W, y)], fill=(8, 10, 14, alpha))

    return Image.alpha_composite(img, overlay)


def _sample_region_brightness(image, x1: int, y1: int, x2: int, y2: int) -> float:
    import numpy as np

    gray = image.convert("L")
    crop = gray.crop((x1, y1, x2, y2))
    arr = np.array(crop)
    return float(arr.mean())


def _choose_text_style(bg, region):
    brightness = _sample_region_brightness(bg, *region)

    if brightness < 120:
        return {
            "fill": (245, 244, 238, 255),
            "shadow": (0, 0, 0, 110),
            "ref_fill": (230, 228, 220, 220),
            "ref_shadow": (0, 0, 0, 90),
        }
    return {
        "fill": (24, 18, 12, 255),
        "shadow": (255, 255, 255, 55),
        "ref_fill": (50, 42, 34, 210),
        "ref_shadow": (255, 255, 255, 40),
    }


def _wrap_text_raw(text: str, font, draw, max_width: int) -> list[str]:
    """
    Wrap Arabic text in logical reading order (top -> bottom),
    while avoiding ugly cases like:
        "جيدها حبل من مسد"
        "في"
    by rebalancing lines when possible.
    """
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = []

    for word in words:
        candidate = " ".join(current + [word])
        bb = draw.textbbox((0, 0), candidate, font=font)
        width = bb[2] - bb[0]

        if width <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    # Rebalance very short last line by moving one word from previous line
    while len(lines) >= 2:
        last_words = lines[-1].split()
        prev_words = lines[-2].split()

        if len(last_words) >= 2:
            break
        if len(prev_words) <= 2:
            break

        moved_word = prev_words.pop()
        candidate_last = " ".join([moved_word] + last_words)

        bb = draw.textbbox((0, 0), candidate_last, font=font)
        if (bb[2] - bb[0]) <= max_width:
            lines[-2] = " ".join(prev_words)
            lines[-1] = candidate_last
        else:
            break

    return [line for line in lines if line.strip()] or [text]


def _fit_font_and_lines(raw_text, font_path, max_w, max_h, draw, start_size=FONT_SIZE):
    from PIL import ImageFont

    size = start_size
    while size >= 42:
        try:
            font = ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        raw_lines = _wrap_text_raw(raw_text, font, draw, max_w)

        # Measure a taller Arabic sample for safer spacing
        sample_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        bb = draw.textbbox((0, 0), sample_text, font=font)
        glyph_h = bb[3] - bb[1]

        # Better line spacing for Arabic with tashkeel
        line_gap = max(22, int(size * 0.26))
        line_h = glyph_h + line_gap

        total_h = line_h * len(raw_lines)

        if total_h <= max_h and len(raw_lines) <= 4:
            return font, raw_lines, line_h

        size -= 4

    try:
        font = ImageFont.truetype(str(font_path), 42) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    raw_lines = _wrap_text_raw(raw_text, font, draw, max_w)
    sample_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    bb = draw.textbbox((0, 0), sample_text, font=font)
    glyph_h = bb[3] - bb[1]
    line_gap = max(18, int(42 * 0.22))
    line_h = glyph_h + line_gap

    return font, raw_lines, line_h


def _fits_text_block(raw_text, font_path, max_w, max_h, draw, start_size=94, max_lines=4):
    """
    Check whether a text block can fit inside the allowed area.
    Returns (fits, font, raw_lines, line_h)
    """
    from PIL import ImageFont

    size = start_size
    while size >= 42:
        try:
            font = ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        raw_lines = _wrap_text_raw(raw_text, font, draw, max_w)
        bb = draw.textbbox((0, 0), "ا", font=font)
        line_h = (bb[3] - bb[1]) + 20
        total_h = line_h * len(raw_lines)

        if total_h <= max_h and len(raw_lines) <= max_lines:
            return True, font, raw_lines, line_h

        size -= 4

    return False, None, None, None


def _build_cinematic_chunks(raw_text, font_path, draw, max_w, max_h, start_size=94, max_lines=4):
    """
    Split the ayah by actual visual fit, not by naive word count.
    Each chunk is the largest sequential group of words that fits
    in the allowed area.
    """
    words = raw_text.split()
    chunks = []

    i = 0
    while i < len(words):
        best_chunk = None
        best_j = i

        for j in range(i + 1, len(words) + 1):
            candidate = " ".join(words[i:j])
            fits, _, _, _ = _fits_text_block(
                candidate,
                font_path=font_path,
                max_w=max_w,
                max_h=max_h,
                draw=draw,
                start_size=start_size,
                max_lines=max_lines,
            )

            if fits:
                best_chunk = candidate
                best_j = j
            else:
                break

        if not best_chunk:
            best_chunk = words[i]
            best_j = i + 1

        chunks.append(best_chunk)
        i = best_j

    return chunks


def _safe_draw_text(draw, x, y, text, primary_font, fallback_font, fill, shadow):
    try:
        draw.text((x + 2, y + 2), text, font=primary_font, fill=shadow)
        draw.text((x, y), text, font=primary_font, fill=fill)
    except Exception:
        draw.text((x + 2, y + 2), text, font=fallback_font, fill=shadow)
        draw.text((x, y), text, font=fallback_font, fill=fill)


def _render_chunk_frame(
    bg,
    chunk_text: str,
    surah_text: str,
    font_path: Optional[Path],
    fallback_font_path: Optional[Path],
    style: dict,
) -> Optional[Path]:
    try:
        from PIL import ImageDraw, ImageFont

        frame = bg.copy()
        draw = ImageDraw.Draw(frame, "RGBA")

        max_w = int(W * 0.74)
        max_h = int(H * 0.20)

        main_font, raw_lines, line_h = _fit_font_and_lines(
            chunk_text, font_path, max_w, max_h, draw, start_size=94
        )

        try:
            fallback_main_font = (
                ImageFont.truetype(str(fallback_font_path), main_font.size)
                if fallback_font_path else main_font
            )
        except Exception:
            fallback_main_font = main_font

        shaped_lines = [_shape_arabic(line) for line in raw_lines]

        total_h = line_h * len(shaped_lines)
        start_y = int(H * 0.42) - (total_h // 2)

        for i, line in enumerate(shaped_lines):
            bb = draw.textbbox((0, 0), line, font=main_font)
            lw = bb[2] - bb[0]
            lx = (W - lw) // 2
            ly = start_y + i * line_h

            _safe_draw_text(
                draw, lx, ly, line, main_font, fallback_main_font,
                style["fill"], style["shadow"]
            )

        try:
            ref_font = ImageFont.truetype(str(font_path), 34) if font_path else ImageFont.load_default()
        except Exception:
            ref_font = ImageFont.load_default()

        try:
            fallback_ref_font = (
                ImageFont.truetype(str(fallback_font_path), 34)
                if fallback_font_path else ref_font
            )
        except Exception:
            fallback_ref_font = ref_font

        shaped_ref = _shape_arabic(surah_text)
        rbb = draw.textbbox((0, 0), shaped_ref, font=ref_font)
        rx = (W - (rbb[2] - rbb[0])) // 2
        ry = int(H * 0.82)

        _safe_draw_text(
            draw, rx, ry, shaped_ref, ref_font, fallback_ref_font,
            style["ref_fill"], style["ref_shadow"]
        )

        out = Path(tempfile.mktemp(suffix=".png"))
        frame.convert("RGB").save(str(out), "PNG", optimize=True)
        return out

    except Exception as e:
        log.error(f"Chunk frame rendering error: {e}")
        return None


def _generate_frames(
    ayah: dict,
    font_path: Optional[Path],
    fallback_font_path: Optional[Path],
    bg_path: Path
) -> list[Path]:
    from PIL import ImageDraw

    bg = _prepare_background(bg_path)

    text_region = (
        int(W * 0.14),
        int(H * 0.32),
        int(W * 0.86),
        int(H * 0.60),
    )
    style = _choose_text_style(bg, text_region)

    raw_text = _clean_quran_text(ayah["arabic_text"])

    temp_img = bg.copy()
    temp_draw = ImageDraw.Draw(temp_img, "RGBA")

    max_w = int(W * 0.74)
    max_h = int(H * 0.20)

    chunks = _build_cinematic_chunks(
        raw_text=raw_text,
        font_path=font_path,
        draw=temp_draw,
        max_w=max_w,
        max_h=max_h,
        start_size=94,
        max_lines=4,
    )

    surah_id = int(ayah["surah_id"])
    surah_name = ayah.get("surah_name_ar") or SURAH_NAMES_AR.get(surah_id, str(surah_id))
    surah_text = f"سورة {surah_name} • الآية {ayah['ayah_number']}"

    frames = []
    for chunk in chunks:
        frame = _render_chunk_frame(
            bg, chunk, surah_text, font_path, fallback_font_path, style
        )
        if frame:
            frames.append(frame)

    return frames


def _encode_video(frames: list[Path], audio: Path, duration: float, out: Path) -> bool:
    if not frames:
        log.error("No frames to encode")
        return False

    min_segment = 1.8
    if duration / len(frames) < min_segment:
        log.warning(
            f"Too many chunks for duration={duration:.2f}s. "
            f"Reducing chunk count may improve readability."
        )

    segment_duration = duration / len(frames)
    fade_d = min(0.6, max(0.25, segment_duration * 0.22))

    inputs = []
    filters = []

    for i, frame in enumerate(frames):
        inputs += ["-loop", "1", "-t", f"{segment_duration:.3f}", "-i", str(frame)]
        filters.append(
            f"[{i}:v]fps={VIDEO_FPS},scale={W}:{H},"
            f"fade=t=in:st=0:d={fade_d:.2f},"
            f"fade=t=out:st={max(0, segment_duration - fade_d):.2f}:d={fade_d:.2f}"
            f"[v{i}]"
        )

    concat_inputs = "".join(f"[v{i}]" for i in range(len(frames)))
    filter_complex = ";".join(filters) + f";{concat_inputs}concat=n={len(frames)}:v=1:a=0[outv]"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", str(audio),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{len(frames)}:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", str(VIDEO_FPS),
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        str(out),
    ]

    log.info("Encoding cinematic MP4…")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        if res.returncode != 0:
            log.error(f"FFmpeg error:\n{res.stderr[-2500:]}")
            return False

        log.info(f"Encoded: {out.name} ({out.stat().st_size // 1024} KB)")
        return True

    except subprocess.TimeoutExpired:
        log.error("FFmpeg timed out")
        return False
    except Exception as e:
        log.error(f"FFmpeg exception: {e}")
        return False

def get_cinematic_chunks_for_text(raw_text: str) -> list[str]:
    """
    Return the actual chunks that would be used for rendering,
    using the same layout-fit logic as the video generator.
    """
    from PIL import Image, ImageDraw

    cleaned_text = _clean_quran_text(raw_text)

    font_path, _ = _find_fonts()

    temp_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img, "RGBA")

    max_w = int(W * 0.74)
    max_h = int(H * 0.20)

    chunks = _build_cinematic_chunks(
        raw_text=cleaned_text,
        font_path=font_path,
        draw=temp_draw,
        max_w=max_w,
        max_h=max_h,
        start_size=94,
        max_lines=4,
    )

    return chunks

def generate_video(ayah: dict, audio_path: Path, duration: float) -> Optional[Path]:
    key = ayah["key"].replace(":", "_")
    out_path = VIDEOS_DIR / f"reel_{key}.mp4"

    if out_path.exists() and out_path.stat().st_size > 50_000:
        log.info(f"Reusing cached: {out_path}")
        return out_path

    font_path, fallback_font_path = _find_fonts()
    if not font_path:
        log.warning("No custom Arabic font found — using default font")

    bg_path = _pick_background_image()
    if not bg_path:
        log.error("No background images found in assets/backgrounds/")
        return None

    log.info(f"Using background image: {bg_path.name}")

    frames = _generate_frames(ayah, font_path, fallback_font_path, bg_path)
    if not frames:
        log.error("Failed to generate frames")
        return None

    try:
        ok = _encode_video(frames, audio_path, duration, out_path)
        return out_path if ok else None
    finally:
        for frame in frames:
            frame.unlink(missing_ok=True)