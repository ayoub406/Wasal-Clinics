# عيادات وصال — منصة حجز المواعيد الطبية

موقع لحجز المواعيد الطبية عن بُعد، مبني بلغة **Python (Flask)** وقاعدة بيانات
**Neon PostgreSQL**. يدعم اللغتين العربية والإنجليزية، الوضع الليلي/النهاري،
تعدد الأقسام الطبية، لوحة تحكم للإدارة، وإشعارات واتساب تلقائية عند اعتماد الموعد.

---

## 1. المزايا

- حجز موعد من أي مكان دون حساب مسبق (الاسم + رقم الهاتف كافيان).
- أقسام طبية متعددة (عظام، أسنان، باطنة، جلدية، أطفال...) قابلة للتعديل من لوحة التحكم.
- لوحة تحكم للإدارة: مراجعة الطلبات، اعتماد موعد نهائي (تاريخ ووقت)، أو رفض الطلب.
- عند اعتماد/رفض الموعد تُرسل رسالة تلقائية للمريض عبر **واتساب** (Meta WhatsApp Cloud API).
- تصميم "زجاجي" راقٍ بلوحة ألوان أبيض/سماوي، وضع ليلي كامل، ودعم RTL/LTR حسب اللغة.
- متجاوب بالكامل مع كل أحجام الشاشات (جوال، تابلت، شاشات كبيرة).
- إعداد قاعدة بيانات جاهز لـ Neon Serverless PostgreSQL مع Connection Pooling
  لتحمّل عدد كبير من الزوار في آنٍ واحد.
- سكربت نسخ احتياطي (`scripts/backup_db.sh`) بالإضافة إلى ميزات Neon المدمجة
  للنسخ الاحتياطي التلقائي ونقاط الاسترجاع الزمنية (PITR).

---

## 2. هيكل المشروع

```
medical_booking/
├── app/
│   ├── admin/          # لوحة تحكم الإدارة (مراجعة/اعتماد/رفض المواعيد)
│   ├── auth/           # تسجيل دخول/خروج المشرف
│   ├── booking/        # نموذج الحجز العام + صفحة "مواعيدي"
│   ├── main/           # الصفحة الرئيسية
│   ├── services/       # خدمة إرسال واتساب
│   ├── static/         # CSS و JS
│   ├── templates/      # قوالب Jinja2
│   ├── models.py       # نماذج قاعدة البيانات (SQLAlchemy)
│   ├── translations.py # قاموس الترجمة عربي/إنجليزي
│   └── cli.py          # أوامر Flask CLI (seed-admin, seed-departments, init-db)
├── scripts/backup_db.sh
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

---

## 3. التشغيل محليًا

```bash
# 1) إنشاء بيئة افتراضية وتثبيت المتطلبات
python3 -m venv venv
source venv/bin/activate        # على ويندوز: venv\Scripts\activate
pip install -r requirements.txt

# 2) نسخ ملف الإعدادات وتعديله
cp .env.example .env
# افتح .env وضع رابط قاعدة بيانات Neon الخاص بك (DATABASE_URL)

# 3) إنشاء الجداول والبيانات الأولية
flask init-db
flask seed-admin
flask seed-departments

# 4) تشغيل الخادم
python run.py
# افتح المتصفح على http://localhost:5000
```

بيانات دخول لوحة التحكم الافتراضية (عدّلها فورًا من `.env` قبل النشر):
- الرابط: `/auth/login`
- المستخدم: القيمة في `DEFAULT_ADMIN_USERNAME` (افتراضيًا `admin`)
- كلمة المرور: القيمة في `DEFAULT_ADMIN_PASSWORD`

---

## 4. ربط قاعدة بيانات Neon PostgreSQL

1. أنشئ مشروعًا جديدًا على [neon.tech](https://neon.tech).
2. من لوحة التحكم، انسخ **Connection string** (اختر Pooled connection للاستخدام العام).
3. ضعه في `.env`:
   ```
   DATABASE_URL=postgresql://USER:PASSWORD@ep-xxxx.neon.tech/dbname?sslmode=require
   DATABASE_URL_DIRECT=postgresql://USER:PASSWORD@ep-xxxx-pooler.neon.tech/dbname?sslmode=require
   ```
4. شغّل `flask init-db` لإنشاء الجداول (أو استخدم `flask db upgrade` إذا فعّلت Flask-Migrate).

> إعدادات `SQLALCHEMY_ENGINE_OPTIONS` في `config.py` مضبوطة مسبقًا (pool_size,
> max_overflow, pool_pre_ping) لتحمل عدد كبير من الزيارات المتزامنة والتعامل
> مع إغلاق Neon للاتصالات الخاملة تلقائيًا.

---

## 5. تفعيل إشعارات واتساب

الخدمة تستخدم **Meta WhatsApp Cloud API** (الرسمية من فيسبوك/ميتا، مجانية ضمن حد شهري):

1. أنشئ تطبيق على [developers.facebook.com](https://developers.facebook.com) من نوع WhatsApp.
2. احصل على `Phone Number ID` و `Access Token` دائم.
3. في `.env`:
   ```
   WHATSAPP_ENABLED=true
   WHATSAPP_PHONE_NUMBER_ID=xxxxxxxxx
   WHATSAPP_ACCESS_TOKEN=xxxxxxxxx
   ```
4. عند `WHATSAPP_ENABLED=false` (الوضع الافتراضي)، تُطبع الرسائل في سجل الخادم
   فقط، وهذا مفيد أثناء التطوير والاختبار دون الحاجة لحساب واتساب فعلي.

الكود المسؤول: `app/services/notifications.py` — يمكن استبداله بسهولة بمزود آخر
(Twilio مثلًا) دون تعديل بقية النظام.

---

## 6. النشر (Deployment)

- استخدم **gunicorn** كخادم WSGI للإنتاج:
  ```bash
  gunicorn -w 4 -k gthread --threads 4 -b 0.0.0.0:8000 run:app
  ```
  عدّل عدد العمال (`-w`) حسب موارد الخادم لتحمّل عدد أكبر من الزوار المتزامنين.
- ضع Nginx أو أي CDN أمام التطبيق لتقديم الملفات الثابتة (`app/static`) وتفعيل HTTPS.
- منصات مقترحة تدعم Flask + Neon مباشرة: Render, Railway, Fly.io, أو أي VPS.
- فعّل متغيرات البيئة نفسها الموجودة في `.env` على منصة النشر (لا ترفع `.env` نفسه).

---

## 7. النسخ الاحتياطي

- Neon يوفر نسخًا احتياطية تلقائية ونقاط استرجاع زمنية (Point-in-Time Recovery)
  من لوحة التحكم مباشرة — فعّلها من إعدادات المشروع.
- بالإضافة إلى ذلك، يوجد سكربت `scripts/backup_db.sh` لعمل نسخة `.sql.gz`
  يوميًا عبر `pg_dump` والاحتفاظ بآخر 14 نسخة. أضِفه إلى `cron`:
  ```
  0 3 * * *  /path/to/medical_booking/scripts/backup_db.sh
  ```

---

## 8. التوسّع لاحقًا (اقتراحات)

- إضافة تسجيل دخول اختياري للمرضى (حاليًا الحجز والمتابعة يتمان برقم الهاتف مباشرة، وهذا أسرع للمستخدم).
- إرسال بريد إلكتروني بالإضافة إلى واتساب.
- تقويم مرئي لمواعيد كل طبيب بدل الفترة الصباحية/المسائية فقط.
- صفحة تقييمات المرضى بعد اكتمال الزيارة.
- تفعيل Flask-Migrate الكامل (`flask db init/migrate/upgrade`) بدل `init-db` عند تطور المخطط.

---

## 9. لقطة سريعة على الألوان والخطوط

- الألوان: أبيض `#FFFFFF`، خلفية سماوية ناعمة `#F4FBFC`، سماوي أساسي `#06AED5` إلى `#057A9E`، حبر كتابة أزرق داكن هادئ `#0B2530` (بدل الأسود الصرف) — مع نسخة كاملة للوضع الليلي.
- الخطوط: `Fraunces` (عناوين) + `Inter` (نصوص) بالإنجليزية، و`Cairo` بكل أوزانها للعربية.
