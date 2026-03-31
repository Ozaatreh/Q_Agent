#!/bin/bash
# quick_test.sh - اختبار سريع لجميع المكونات

echo "🔍 فحص المتطلبات الأساسية..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version)
    echo "✅ Python: $PY_VERSION"
else
    echo "❌ Python غير مثبت!"
    exit 1
fi

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    FF_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    echo "✅ FFmpeg: $FF_VERSION"
else
    echo "❌ FFmpeg غير مثبت!"
    exit 1
fi

# Check venv
if [ -d "venv" ]; then
    echo "✅ البيئة الافتراضية موجودة"
else
    echo "⚠️  البيئة الافتراضية غير موجودة - تشغيل setup.sh"
    ./setup.sh
fi

echo ""
echo "🎨 فحص الخطوط..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "assets/NotoNaskhArabic-Bold.ttf" ]; then
    SIZE=$(ls -lh assets/NotoNaskhArabic-Bold.ttf | awk '{print $5}')
    echo "✅ Noto Naskh Arabic Bold: $SIZE"
else
    echo "❌ الخط غير موجود - جاري التحميل..."
    cd assets/
    wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Bold.ttf
    wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf
    cd ..
    echo "✅ تم تحميل الخطوط"
fi

echo ""
echo "⚙️  فحص الإعدادات..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    echo "✅ ملف .env موجود"
    
    # Check if tokens are set
    if grep -q "YOUR_ACCESS_TOKEN_HERE" .env; then
        echo "⚠️  ACCESS_TOKEN غير محدّث - يجب تحديثه!"
    else
        echo "✅ ACCESS_TOKEN محدّث"
    fi
    
    if grep -q "YOUR_BUSINESS_ACCOUNT_ID" .env; then
        echo "⚠️  BUSINESS_ID غير محدّث - يجب تحديثه!"
    else
        echo "✅ BUSINESS_ID محدّث"
    fi
else
    echo "❌ ملف .env غير موجود - جاري الإنشاء..."
    cp .env.example .env 2>/dev/null || echo "INSTAGRAM_ACCESS_TOKEN=YOUR_ACCESS_TOKEN_HERE
INSTAGRAM_BUSINESS_ID=YOUR_BUSINESS_ACCOUNT_ID" > .env
    echo "✅ تم إنشاء .env - يجب تحديثه!"
fi

echo ""
echo "📁 فحص المجلدات..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for dir in output/videos output/audio output/logs; do
    if [ -d "$dir" ]; then
        COUNT=$(ls $dir 2>/dev/null | wc -l)
        echo "✅ $dir ($COUNT ملف)"
    else
        echo "⚠️  $dir غير موجود - جاري الإنشاء..."
        mkdir -p "$dir"
    fi
done

echo ""
echo "🧪 اختبار المكتبات..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

source venv/bin/activate 2>/dev/null || {
    echo "❌ فشل تفعيل البيئة الافتراضية"
    exit 1
}

python3 -c "
import sys
packages = [
    'PIL',
    'requests',
    'arabic_reshaper',
    'bidi',
    'schedule'
]

missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError:
        print(f'❌ {pkg} غير مثبت')
        missing.append(pkg)

if missing:
    print('
⚠️  مكتبات ناقصة - جاري التثبيت...')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    pip install -r requirements.txt -q
    echo "✅ تم تثبيت المكتبات الناقصة"
fi

echo ""
echo "🎬 اختبار إنشاء فيديو تجريبي..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create a simple test
python3 << 'PYTEST'
import sys
sys.path.insert(0, '.')

from modules.ayah_picker import pick_ayah
from modules.logger import get_logger

log = get_logger("test")
log.info("اختبار جلب آية...")

ayah = pick_ayah()
if ayah:
    print(f"✅ تم جلب الآية: {ayah['surah_id']}:{ayah['ayah_number']}")
    print(f"   النص: {ayah['arabic_text'][:50]}...")
else:
    print("❌ فشل جلب الآية")
    sys.exit(1)
PYTEST

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ جميع الفحوصات نجحت!"
    echo ""
    echo "🚀 لتشغيل البرنامج:"
    echo "   source venv/bin/activate"
    echo "   python pipeline.py"
    echo ""
    echo "📖 راجع ملف SETUP_GUIDE_AR.md للتعليمات الكاملة"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ بعض الفحوصات فشلت - راجع الرسائل أعلاه"
    exit 1
fi
