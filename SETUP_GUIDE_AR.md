# 🌙 دليل التشغيل الكامل - Quran Reels Agent

## 📱 نظرة عامة
هذا النظام يقوم **تلقائياً** بـ:
1. اختيار آية قرآنية عشوائية من سور قصيرة
2. تحميل التلاوة الصوتية (مشاري العفاسي)
3. إنشاء فيديو Reel احترافي (1080×1920)
4. كتابة Caption مع التفسير
5. النشر على Instagram تلقائياً
6. **تكرار العملية 3 مرات يومياً** (7 صباحاً، 1 ظهراً، 8 مساءً)

---

## 🔧 الخطوة 1: التحضيرات الأساسية

### 1.1 تثبيت المتطلبات الأساسية

```bash
# على Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg git -y

# على macOS
brew install python ffmpeg git

# تحقق من التثبيت
python3 --version   # يجب أن يكون 3.10 أو أحدث
ffmpeg -version     # للتأكد من وجود FFmpeg
```

### 1.2 تحميل المشروع

```bash
# انتقل للمجلد الذي تريد العمل فيه
cd ~/Desktop

# فك ضغط الملف
unzip quran_reels_agent.zip
cd quran_reels_agent

# اعطاء صلاحيات التنفيذ
chmod +x setup.sh setup_cron.sh
```

---

## 🎯 الخطوة 2: الإعداد التلقائي

```bash
# شغل السكريبت التلقائي
./setup.sh
```

هذا السكريبت يقوم بـ:
- ✅ فحص وجود FFmpeg
- ✅ إنشاء بيئة Python افتراضية (venv)
- ✅ تثبيت جميع المكتبات المطلوبة
- ✅ إنشاء ملف `.env` للإعدادات

---

## 📱 الخطوة 3: إعداد Instagram API

هذه أهم خطوة! بدونها لن يعمل النشر.

### 3.1 إنشاء Facebook App

1. اذهب إلى: https://developers.facebook.com
2. اضغط **Create App** → اختر نوع **Business**
3. املأ البيانات (اسم التطبيق، بريدك)
4. بعد الإنشاء، اضغط **Add Product** → اختر **Instagram Graph API**

### 3.2 ربط حساب Instagram

1. في لوحة التحكم، اذهب لـ **Instagram Graph API** → **Settings**
2. اضغط **Add or Remove Instagram Accounts**
3. سجل دخول بحساب Instagram الذي تريد النشر عليه
4. ⚠️ **مهم جداً**: الحساب يجب أن يكون **Business** أو **Creator**
   - إذا كان شخصياً، حوّله من إعدادات Instagram → Account Type

### 3.3 الحصول على Access Token

```bash
# في المتصفح، افتح:
https://developers.facebook.com/tools/explorer/

# 1. اختر التطبيق الذي أنشأته من القائمة المنسدلة
# 2. اضغط "Generate Access Token"
# 3. اختر الصلاحيات:
#    - instagram_basic
#    - instagram_content_publish
#    - pages_read_engagement
#    - pages_show_list

# 4. اضغط "Generate Token" واحفظه
```

**⚠️ التوكن يستمر 60 يوماً فقط!** سنحتاج تحديثه لاحقاً.

### 3.4 الحصول على Instagram Business Account ID

```bash
# استبدل YOUR_TOKEN بالتوكن الذي حصلت عليه
curl "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_TOKEN"

# النتيجة ستكون مثل:
# {
#   "data": [
#     {
#       "access_token": "...",
#       "id": "123456789",  ← هذا هو Page ID
#       "name": "Your Page Name"
#     }
#   ]
# }

# الآن استخدم Page ID للحصول على Instagram ID:
curl "https://graph.facebook.com/v19.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"

# النتيجة:
# {
#   "instagram_business_account": {
#     "id": "17841987654321"  ← هذا هو Instagram Business ID
#   },
#   "id": "123456789"
# }
```

---

## ⚙️ الخطوة 4: إعداد الملفات

### 4.1 تحديث ملف .env

```bash
nano .env
```

املأ البيانات:

```env
# ضع التوكن الطويل الذي حصلت عليه
INSTAGRAM_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ضع رقم الحساب Instagram Business ID
INSTAGRAM_BUSINESS_ID=17841987654321
```

احفظ الملف: `Ctrl+O` → `Enter` → `Ctrl+X`

### 4.2 تعديل الإعدادات (اختياري)

```bash
nano config/settings.py
```

يمكنك تغيير:

```python
# السور المستخدمة (حالياً: سور قصيرة)
SHORT_SURAH_IDS = [
    1,   # الفاتحة
    112, # الإخلاص
    113, # الفلق
    114, # الناس
    # يمكنك إضافة أي سورة أخرى
]

# القارئ (7 = مشاري العفاسي)
RECITER_ID = 7

# أوقات النشر (بتوقيت السيرفر المحلي)
PUBLISH_TIMES = ["07:00", "13:00", "20:00"]
```

---

## 🚀 الخطوة 5: التشغيل

### 5.1 اختبار يدوي (مرة واحدة)

```bash
# تفعيل البيئة الافتراضية
source venv/bin/activate

# تشغيل البرنامج مرة واحدة
python pipeline.py
```

**ما سيحدث:**
1. سيختار آية عشوائية من السور القصيرة
2. سينزّل صوت التلاوة (~20 ثانية)
3. سينشئ فيديو 1080×1920 (~30 ثانية لإنشاء الفيديو)
4. سيحاول النشر على Instagram
5. ستجد الفيديو في: `output/videos/reel_X_X.mp4`
6. ستجد اللوجات في: `output/logs/2026-03-27.log`

### 5.2 فحص النتيجة

```bash
# شاهد اللوجات
cat output/logs/$(date +%Y-%m-%d).log

# شاهد الفيديوهات المنشأة
ls -lh output/videos/

# شاهد الآيات التي تم نشرها
cat output/published_ayahs.json
```

---

## ⏰ الخطوة 6: التشغيل التلقائي (الجدولة)

لديك 3 خيارات:

### الخيار 1: Python Scheduler (الأسهل)

```bash
# سيظل يعمل في الخلفية ويقوم بالنشر في الأوقات المحددة
nohup python modules/scheduler.py > scheduler.log 2>&1 &

# للتحقق من أنه يعمل
ps aux | grep scheduler.py

# لإيقافه لاحقاً
pkill -f scheduler.py
```

### الخيار 2: Cron (موصى به للإنتاج)

```bash
# سيضيف 3 مهام في cron
./setup_cron.sh

# للتحقق من المهام المضافة
crontab -l

# ستجد:
# 0 7  * * * cd /path/to/quran_reels_agent && /path/to/venv/bin/python pipeline.py
# 0 13 * * * cd /path/to/quran_reels_agent && /path/to/venv/bin/python pipeline.py
# 0 20 * * * cd /path/to/quran_reels_agent && /path/to/venv/bin/python pipeline.py
```

### الخيار 3: تشغيل مباشر على VPS/Server

```bash
# إذا كنت على سيرفر
sudo systemctl enable cron
sudo systemctl start cron

# أو استخدم screen/tmux للتشغيل الدائم
screen -S quran_reels
source venv/bin/activate
python modules/scheduler.py
# اضغط Ctrl+A ثم D للخروج من Screen
```

---

## 🔍 الخطوة 7: المراقبة والصيانة

### 7.1 فحص اللوجات اليومية

```bash
# آخر 50 سطر من لوج اليوم
tail -50 output/logs/$(date +%Y-%m-%d).log

# متابعة اللوج مباشرة
tail -f output/logs/$(date +%Y-%m-%d).log
```

### 7.2 فحص الفيديوهات المنشأة

```bash
# عدد الفيديوهات
ls output/videos/*.mp4 | wc -l

# حجم كل فيديو
ls -lh output/videos/

# شاهد فيديو محدد
ffplay output/videos/reel_112_1.mp4
```

### 7.3 فحص Instagram Publishing

```bash
# شاهد الآيات المنشورة
cat output/published_ayahs.json

# أو بشكل مرتب
python3 -m json.tool output/published_ayahs.json
```

---

## ❌ حل المشاكل الشائعة

### المشكلة 1: "No Arabic font found"

```bash
# حمّل الخط العربي
cd assets/
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Bold.ttf
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf
```

### المشكلة 2: "FFmpeg not found"

```bash
# Ubuntu/Debian
sudo apt install ffmpeg -y

# macOS
brew install ffmpeg

# تحقق
ffmpeg -version
```

### المشكلة 3: "Instagram API Error 190"

معناها: **Access Token منتهي الصلاحية**

```bash
# احصل على توكن جديد من:
https://developers.facebook.com/tools/explorer/

# حدّث ملف .env
nano .env
# غيّر INSTAGRAM_ACCESS_TOKEN
```

### المشكلة 4: "Video too large"

```bash
# افتح video_generator.py
nano modules/video_generator.py

# ابحث عن السطر:
"-crf", "22",

# غيّره إلى:
"-crf", "28",  # حجم أصغر، جودة أقل قليلاً
```

### المشكلة 5: النص العربي غير واضح

**✅ تم الحل!** الكود المُحدّث يستخدم خطوط أكبر.

لكن إذا ما زال غير واضح:

```bash
nano modules/video_generator.py

# ابحث عن:
start_size=110

# زوّده إلى:
start_size=130
```

---

## 📊 مثال على النتيجة

بعد التشغيل، ستحصل على:

### الفيديو
- **الدقة:** 1080×1920 (9:16)
- **المدة:** 15-30 ثانية
- **الحجم:** ~300-500 KB
- **الصوت:** تلاوة مشاري العفاسي

### المحتوى البصري
1. خلفية Deep Space بتدرجات زرقاء داكنة
2. نجوم متلألئة
3. توهج ذهبي في المنتصف
4. البسملة في الأعلى (ذهبي)
5. فواصل ذهبية مزخرفة
6. نص الآية (أبيض كبير وواضح)
7. رقم السورة والآية (ذهبي)
8. "قرآن كريم ✦" في الأسفل

### الـ Caption

```
🌙 قُلْ هُوَ اللَّهُ أَحَدٌ

"Say: He is Allah, the One!"

— سورة الإخلاص، آية 1 —

━━━━━━━━━━━━━━━━
جعل الله هذا التذكير في ميزان حسناتك 🤲

#قرآن #إسلام #تذكير #آيات_قرآنية #القرآن_الكريم #توحيد #الإخلاص
```

---

## 🔄 تحديث Access Token (كل 60 يوم)

```bash
# 1. احصل على توكن جديد
# https://developers.facebook.com/tools/explorer/

# 2. حدّث .env
nano .env

# 3. أعد تشغيل Scheduler
pkill -f scheduler.py
nohup python modules/scheduler.py > scheduler.log 2>&1 &
```

---

## 📈 إحصائيات

بعد أسبوع من التشغيل:
- **عدد المنشورات:** 21 ريل (3 يومياً × 7 أيام)
- **مساحة التخزين:** ~7-10 MB (الفيديوهات)
- **استهلاك API:** ~63 طلب شهرياً (ضمن الحد المجاني)

---

## 🛠️ التخصيصات المتقدمة

### إضافة ترجمة إنجليزية في الفيديو

```python
# في modules/video_generator.py، بعد السطر 191:

# Add English translation below Arabic
trans_text = ayah["translation"]
trans_font = ImageFont.truetype(str(font_path), 32)
trans_y = start_y + total_h + 30
for line in _wrap_text(trans_text, trans_font, draw, text_w):
    bb = draw.textbbox((0, 0), line, font=trans_font)
    lx = (W - (bb[2] - bb[0])) // 2
    draw.text((lx, trans_y), line, font=trans_font, fill=(200, 200, 200, 220))
    trans_y += 40
```

### تغيير القارئ

```python
# في config/settings.py:

RECITER_ID = 5   # عبد الباسط عبد الصمد
# RECITER_ID = 1  # عبد الله بصفر
# RECITER_ID = 2  # عبد الرشيد صوفي
# RECITER_ID = 7  # مشاري العفاسي (الافتراضي)

# قائمة كاملة:
# https://api.quran.com/api/v4/resources/recitations
```

### تغيير الألوان

```python
# في modules/video_generator.py:

gold = (255, 215, 0, 210)        # ذهب أكثر إشراقاً
# gold = (212, 175, 55, 210)     # الافتراضي
# gold = (184, 134, 11, 210)     # ذهب داكن
```

---

## ✅ Checklist النهائية

قبل التشغيل النهائي، تحقق من:

- [ ] Python 3.10+ مثبت
- [ ] FFmpeg مثبت
- [ ] حساب Instagram Business/Creator
- [ ] Facebook App مُنشأ
- [ ] Instagram Graph API مُفعّل
- [ ] Access Token صالح
- [ ] Instagram Business ID صحيح
- [ ] ملف .env محدّث بالبيانات الصحيحة
- [ ] تم اختبار pipeline.py بنجاح
- [ ] الفيديو المُنشأ واضح ومقروء
- [ ] Scheduler يعمل في الخلفية
- [ ] Cron jobs مضافة (إذا استخدمت Cron)

---

## 📞 الدعم والمساعدة

إذا واجهت أي مشكلة:

1. **افحص اللوجات:** `output/logs/YYYY-MM-DD.log`
2. **اختبر FFmpeg:** `ffmpeg -version`
3. **اختبر الخط:** `ls assets/*.ttf`
4. **اختبر API:** استخدم curl للتحقق من Access Token
5. **أعد التشغيل:** `pkill -f scheduler.py && nohup python modules/scheduler.py &`

---

*بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ* 🌙
