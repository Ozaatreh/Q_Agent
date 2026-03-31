#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  setup.sh — One-time setup for Quran Reels Agent
#  Run:  chmod +x setup.sh && ./setup.sh
# ─────────────────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Quran Reels Agent — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. System dependencies ────────────────────────────────────────
echo "[1/4] Checking system dependencies…"
for cmd in ffmpeg ffprobe python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "  ✗ $cmd not found. Install it first."
        echo "    Ubuntu/Debian:  sudo apt install ffmpeg python3"
        exit 1
    fi
    echo "  ✓ $cmd found"
done

# ── 2. Python virtual environment ────────────────────────────────
echo "[2/4] Setting up Python virtual environment…"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✓ Created venv"
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✓ Dependencies installed"

# ── 3. Download Amiri font ────────────────────────────────────────
echo "[3/4] Downloading Amiri Arabic font…"
FONT_URL="https://github.com/alif-type/amiri/releases/download/1.000/amiri-1.000.zip"
FONT_DIR="assets"
mkdir -p "$FONT_DIR"

if [ ! -f "$FONT_DIR/Amiri-Regular.ttf" ]; then
    # Try apt first
    if sudo apt-get install -y fonts-amiri -q 2>/dev/null; then
        echo "  ✓ Amiri installed via apt"
    else
        echo "  Downloading from GitHub…"
        curl -L "$FONT_URL" -o /tmp/amiri.zip 2>/dev/null || true
        if [ -f /tmp/amiri.zip ]; then
            unzip -q /tmp/amiri.zip -d /tmp/amiri_font
            find /tmp/amiri_font -name "Amiri-Regular.ttf" -exec cp {} "$FONT_DIR/" \;
            rm -rf /tmp/amiri.zip /tmp/amiri_font
            echo "  ✓ Amiri-Regular.ttf downloaded"
        else
            echo "  ⚠  Could not download Amiri. A system font will be used as fallback."
        fi
    fi
else
    echo "  ✓ Amiri font already present"
fi

# ── 4. Create .env if missing ────────────────────────────────────
echo "[4/4] Checking .env file…"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✓ Created .env from template"
    echo "  ⚠  Please edit .env and fill in your Instagram credentials!"
else
    echo "  ✓ .env exists"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your Instagram API credentials"
echo "  2. Test: source venv/bin/activate && python pipeline.py"
echo "  3. Schedule: ./setup_cron.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
