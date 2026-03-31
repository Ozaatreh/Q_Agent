# ❓ الأسئلة الشائعة وحل المشاكل - FAQ & Troubleshooting

## 🎯 أسئلة عامة

### س: كم يستغرق تشغيل البرنامج لأول مرة؟
**ج:** حوالي 2-5 دقائق:
- تحميل الخطوط: ~30 ثانية
- تثبيت المكتبات: ~1-2 دقيقة
- أول تشغيل وإنشاء فيديو: ~1-2 دقيقة

### س: كم مرة ينشر البرنامج يومياً؟
**ج:** 3 مرات افتراضياً (7 صباحاً، 1 ظهراً، 8 مساءً). يمكنك تغيير الأوقات في `config/settings.py`:
```python
PUBLISH_TIMES = ["07:00", "13:00", "20:00"]
```

### س: هل يكرر نفس الآيات؟
**ج:** لا أبداً! كل آية تُنشر مرة واحدة فقط. يتم حفظ السجل في `output/published_ayahs.json`.

### س: كم يستهلك من مساحة التخزين؟
**ج:**
- كل فيديو: ~300-500 KB
- كل ملف صوتي: ~50-150 KB
- شهرياً (90 فيديو): ~35-60 MB
- بعد سنة: ~450-700 MB

### س: هل يعمل على Windows؟
**ج:** نعم، لكن يحتاج:
1. تثبيت Python من python.org
2. تثبيت FFmpeg من ffmpeg.org
3. استخدام PowerShell أو WSL بدلاً من bash

---

## 🔴 مشاكل التثبيت والإعداد

### ❌ المشكلة: `bash: ./setup.sh: Permission denied`

**الحل:**
```bash
chmod +x setup.sh
chmod +x setup_cron.sh
chmod +x quick_test.sh
./setup.sh
```

---

### ❌ المشكلة: `python: command not found`

**الحل:**
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv -y

# macOS
brew install python3

# تحقق
python3 --version
```

---

### ❌ المشكلة: `ffmpeg: not found`

**الحل:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg -y

# macOS
brew install ffmpeg

# تحقق من التثبيت
ffmpeg -version
which ffmpeg
```

---

### ❌ المشكلة: `ModuleNotFoundError: No module named 'PIL'`

**الحل:**
```bash
source venv/bin/activate
pip install -r requirements.txt

# أو يدوياً
pip install Pillow arabic-reshaper python-bidi requests schedule python-dotenv
```

---

### ❌ المشكلة: `FileNotFoundError: [Errno 2] No such file or directory: 'assets/'`

**الحل:**
```bash
mkdir -p assets output/videos output/audio output/logs
cd assets
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Bold.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf
cd ..
```

---

## 🔴 مشاكل Instagram API

### ❌ المشكلة: `Error 190 - Access token has expired`

**السبب:** Access Token صالح لـ60 يوماً فقط

**الحل:**
```bash
# 1. اذهب إلى
https://developers.facebook.com/tools/explorer/

# 2. اختر تطبيقك
# 3. اضغط "Generate Access Token"
# 4. اختر الصلاحيات:
#    - instagram_basic
#    - instagram_content_publish
#    - pages_read_engagement

# 5. انسخ التوكن الجديد

# 6. حدّث .env
nano .env
# غيّر INSTAGRAM_ACCESS_TOKEN

# 7. أعد تشغيل Scheduler
pkill -f scheduler.py
nohup python modules/scheduler.py > scheduler.log 2>&1 &
```

**نصيحة:** سجّل تاريخ انتهاء التوكن واضبط تذكيراً كل 50 يوم لتحديثه.

---

### ❌ المشكلة: `Error 100 - Invalid parameter`

**الأسباب المحتملة:**
1. Instagram Business ID خطأ
2. الحساب ليس Business/Creator
3. Access Token لا يملك الصلاحيات

**الحل:**
```bash
# 1. تحقق من نوع الحساب
# اذهب لإعدادات Instagram → Account → Switch to Professional Account

# 2. احصل على Instagram Business ID الصحيح
curl "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_TOKEN"

# ستحصل على Page ID، استخدمه:
curl "https://graph.facebook.com/v19.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"

# 3. حدّث .env
nano .env
# ضع الـ instagram_business_account.id في INSTAGRAM_BUSINESS_ID
```

---

### ❌ المشكلة: `Error 368 - Temporarily blocked for spamming`

**السبب:** Instagram اعتبر النشر سبام (نادر مع 3 منشورات يومياً)

**الحل:**
```bash
# 1. قلل عدد المنشورات مؤقتاً
nano config/settings.py
# غيّر PUBLISH_TIMES = ["13:00"]  # مرة واحدة يومياً

# 2. انتظر 24-48 ساعة
# 3. ارجع للنشر الطبيعي تدريجياً
```

---

### ❌ المشكلة: `Video URL not accessible`

**السبب:** Instagram لا يستطيع الوصول للفيديو

**الحلول:**

**الحل 1: استخدام Resumable Upload (موصى به)**
```python
# في config/settings.py
# تأكد أن VIDEO_PUBLIC_URL غير موجود أو فارغ
# VIDEO_PUBLIC_URL = ""  # استخدم resumable upload
```

**الحل 2: رفع على S3/Cloudflare R2**
```bash
# ثبّت AWS CLI
pip install awscli

# رفع الفيديو
aws s3 cp output/videos/reel.mp4 s3://your-bucket/reel.mp4 --acl public-read

# حدّث settings.py
VIDEO_PUBLIC_URL = "https://your-bucket.s3.amazonaws.com/reel.mp4"
```

---

## 🔴 مشاكل الفيديو والنص

### ❌ المشكلة: النص العربي مقلوب أو مفصول

**السبب:** عدم وجود `arabic_reshaper` و `python-bidi`

**الحل:**
```bash
source venv/bin/activate
pip install arabic-reshaper python-bidi --upgrade

# اختبر
python3 -c "
import arabic_reshaper
from bidi.algorithm import get_display
text = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'
reshaped = arabic_reshaper.reshape(text)
bidi_text = get_display(reshaped)
print(bidi_text)
"
```

---

### ❌ المشكلة: النص صغير جداً وغير مقروء

**السبب:** إصدار قديم من الكود

**✅ الحل:** استخدم الكود المُحدّث!

التحديثات:
- البسملة: 38 → 56 بكسل
- النص الرئيسي: يبدأ من 110 بكسل
- مرجع السورة: 42 → 54 بكسل
- الحد الأدنى: 24 → 48 بكسل

**إذا ما زال صغيراً:**
```bash
nano modules/video_generator.py

# ابحث عن:
start_size=110

# زوّده إلى:
start_size=140
```

---

### ❌ المشكلة: `RuntimeError: No Arabic font found`

**الحل:**
```bash
# حمّل الخط مباشرة
cd assets/
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Bold.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf

# تحقق
ls -lh *.ttf

# يجب أن ترى:
# NotoNaskhArabic-Bold.ttf     (~177 KB)
# NotoNaskhArabic-Regular.ttf  (~172 KB)
```

---

### ❌ المشكلة: الفيديو أسود بالكامل

**الحل:**
```bash
# افحص اللوج
cat output/logs/$(date +%Y-%m-%d).log | grep -i error

# اختبار FFmpeg
ffmpeg -f lavfi -i color=c=blue:s=1080x1920:d=5 -c:v libx264 test.mp4

# إذا نجح، المشكلة في الكود
# راجع modules/video_generator.py السطر 230-260
```

---

### ❌ المشكلة: الصوت غير متزامن مع الفيديو

**السبب:** مدة الفيديو لا تطابق مدة الصوت

**الحل:**
```bash
# افحص مدة الصوت
ffprobe -i output/audio/112_1_reciter7.mp3 -show_entries format=duration -v quiet -of csv="p=0"

# إذا كانت المدة صحيحة، تأكد من السطر:
# في video_generator.py:
"-t", str(duration),  # يجب أن تكون نفس مدة الصوت
```

---

## 🔴 مشاكل الجدولة والتشغيل

### ❌ المشكلة: Scheduler لا يعمل

**الحل:**
```bash
# تحقق من العملية
ps aux | grep scheduler.py

# إذا لم تكن موجودة، شغّلها
source venv/bin/activate
nohup python modules/scheduler.py > scheduler.log 2>&1 &

# راقب اللوج
tail -f scheduler.log
```

---

### ❌ المشكلة: Cron job لا يعمل

**الحل:**
```bash
# تحقق من الـ cron jobs
crontab -l

# إذا كانت موجودة، افحص اللوج
grep CRON /var/log/syslog  # Ubuntu/Debian
tail -f /var/log/cron       # CentOS/RHEL

# تأكد من المسارات الكاملة
crontab -e

# مثال صحيح:
0 7 * * * cd /home/user/quran_reels_agent && /home/user/quran_reels_agent/venv/bin/python pipeline.py >> /home/user/quran_reels_agent/cron.log 2>&1
```

---

### ❌ المشكلة: البرنامج يتوقف بعد فترة

**الأسباب المحتملة:**
1. السيرفر يُعاد تشغيله
2. نفاد الذاكرة
3. Crash غير متوقع

**الحل:**
```bash
# استخدم systemd service (أفضل للإنتاج)
sudo nano /etc/systemd/system/quran-reels.service

# أضف:
[Unit]
Description=Quran Reels Agent
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/quran_reels_agent
ExecStart=/path/to/quran_reels_agent/venv/bin/python modules/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# فعّل الـ service
sudo systemctl daemon-reload
sudo systemctl enable quran-reels
sudo systemctl start quran-reels

# راقبه
sudo systemctl status quran-reels
sudo journalctl -u quran-reels -f
```

---

## 🔴 مشاكل الأداء

### ❌ المشكلة: الفيديو كبير جداً (> 5 MB)

**الحل:**
```bash
nano modules/video_generator.py

# ابحث عن:
"-crf", "22",

# غيّره إلى:
"-crf", "28",  # جودة أقل، حجم أصغر

# أو:
"-crf", "26",  # توازن جيد
```

**CRF Guide:**
- 18 = جودة عالية جداً (~2-3 MB)
- 22 = جودة عالية (~500 KB) ← **الافتراضي**
- 26 = جودة جيدة (~300 KB)
- 28 = جودة متوسطة (~200 KB)

---

### ❌ المشكلة: إنشاء الفيديو بطيء (> 60 ثانية)

**الحل:**
```bash
nano modules/video_generator.py

# ابحث عن:
"-preset", "medium",

# غيّره إلى:
"-preset", "fast",     # أسرع، حجم أكبر قليلاً
# أو:
"-preset", "veryfast", # الأسرع، حجم أكبر
```

**Preset Guide:**
- ultrafast = أسرع، أكبر حجم
- veryfast
- fast
- medium ← **الافتراضي** (توازن جيد)
- slow = أبطأ، أفضل ضغط
- veryslow = الأبطأ، أفضل جودة/حجم

---

## 🔴 مشاكل الشبكة والـ API

### ❌ المشكلة: `ConnectionError: Failed to download audio`

**الحل:**
```bash
# اختبر الاتصال بالإنترنت
ping -c 4 google.com

# اختبر Quran.com API
curl "https://api.quran.com/api/v4/verses/by_key/1:1?words=true&audio=7"

# إذا فشل، ربما API معطل مؤقتاً
# انتظر 5-10 دقائق وحاول مرة أخرى
```

---

### ❌ المشكلة: `TimeoutError` أثناء التحميل

**الحل:**
```bash
# زيادة Timeout
nano modules/audio_fetcher.py

# ابحث عن:
response = requests.get(url, timeout=30)

# غيّره إلى:
response = requests.get(url, timeout=60)  # دقيقة واحدة
```

---

## 🔴 مشاكل اللوجات والتتبع

### ❌ المشكلة: اللوجات لا تظهر

**الحل:**
```bash
# تحقق من المجلد
ls -la output/logs/

# إذا كان فارغاً، أنشئه
mkdir -p output/logs

# تحقق من الصلاحيات
chmod 755 output/logs

# اختبار يدوي
python3 << EOF
from modules.logger import get_logger
log = get_logger("test")
log.info("اختبار اللوج")
EOF

# يجب أن تظهر في:
cat output/logs/$(date +%Y-%m-%d).log
```

---

## 📊 أدوات المراقبة

### مراقبة المساحة
```bash
# حجم جميع الملفات
du -sh output/*

# حجم كل نوع
du -sh output/videos/
du -sh output/audio/
du -sh output/logs/
```

### مراقبة العمليات
```bash
# عمليات Python النشطة
ps aux | grep python

# استهلاك CPU/Memory
top -p $(pgrep -f scheduler.py)
```

### مراقبة الـ API Calls
```bash
# عدد المنشورات
cat output/published_ayahs.json | grep -c "published_at"

# آخر منشور
python3 -m json.tool output/published_ayahs.json | tail -20
```

---

## ✅ نصائح الصيانة

### يومياً
```bash
# افحص اللوج
tail -30 output/logs/$(date +%Y-%m-%d).log
```

### أسبوعياً
```bash
# افحص المساحة
du -sh output/*

# افحص عدد المنشورات
cat output/published_ayahs.json | grep -c "published_at"

# نظّف الملفات القديمة (اختياري)
find output/videos/ -mtime +30 -delete  # مسح الفيديوهات الأقدم من 30 يوم
find output/audio/ -mtime +30 -delete   # مسح الصوت الأقدم من 30 يوم
```

### شهرياً
```bash
# حدّث Access Token (كل 50-60 يوم)
# راجع قسم "Error 190" أعلاه

# افحص التحديثات
cd quran_reels_agent
git pull  # إذا كنت تستخدم Git

# حدّث المكتبات
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## 🆘 ما زلت أواجه مشكلة؟

### الخطوات النهائية:

1. **افحص اللوجات بالكامل:**
```bash
cat output/logs/$(date +%Y-%m-%d).log
```

2. **شغّل الاختبار السريع:**
```bash
./quick_test.sh
```

3. **اختبر يدوياً خطوة بخطوة:**
```bash
source venv/bin/activate
python3 << EOF
from modules.ayah_picker import pick_ayah
from modules.audio_fetcher import fetch_audio
from modules.video_generator import generate_video

ayah = pick_ayah()
print(f"Ayah: {ayah}")

audio_path, duration = fetch_audio(ayah)
print(f"Audio: {audio_path}, Duration: {duration}")

video_path = generate_video(ayah, audio_path, duration)
print(f"Video: {video_path}")
EOF
```

4. **أعد التثبيت من الصفر:**
```bash
rm -rf venv/
./setup.sh
source venv/bin/activate
python pipeline.py
```

---

*إذا استمرت المشكلة، راجع اللوجات وابحث عن رسالة الخطأ الدقيقة* 🔍
