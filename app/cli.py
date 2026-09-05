import click
from app.extensions import db
from app.models import Admin, Department


DEFAULT_DEPARTMENTS = [
    dict(slug="orthopedics", icon="bone",
         name_ar="العظام", name_en="Orthopedics",
         description_ar="تشخيص وعلاج إصابات وأمراض العظام والمفاصل والعمود الفقري.",
         description_en="Diagnosis and treatment of bone, joint and spine conditions."),
    dict(slug="dental", icon="tooth",
         name_ar="الأسنان", name_en="Dental",
         description_ar="طب أسنان شامل من الحشوات والتقويم إلى زراعة الأسنان.",
         description_en="Comprehensive dental care from fillings and braces to implants."),
    dict(slug="internal-medicine", icon="pulse",
         name_ar="الباطنة", name_en="Internal Medicine",
         description_ar="متابعة الأمراض المزمنة والفحوصات الداخلية العامة.",
         description_en="Chronic disease management and general internal check-ups."),
    dict(slug="dermatology", icon="leaf",
         name_ar="الجلدية والتجميل", name_en="Dermatology",
         description_ar="عناية بالبشرة والشعر وعلاجات تجميلية متقدمة.",
         description_en="Skin and hair care with advanced cosmetic treatments."),
    dict(slug="pediatrics", icon="baby",
         name_ar="الأطفال", name_en="Pediatrics",
         description_ar="رعاية صحية متكاملة للرضع والأطفال حتى سن المراهقة.",
         description_en="Complete healthcare for infants, children and teens."),
    dict(slug="obgyn", icon="heart",
         name_ar="النساء والتوليد", name_en="OB-GYN",
         description_ar="متابعة الحمل والولادة وصحة المرأة في جميع المراحل.",
         description_en="Pregnancy care, delivery and women's health at every stage."),
    dict(slug="cardiology", icon="heartbeat",
         name_ar="القلب", name_en="Cardiology",
         description_ar="تشخيص ومتابعة أمراض القلب والشرايين بأحدث الأجهزة.",
         description_en="Diagnosis and monitoring of heart and vascular conditions."),
    dict(slug="ophthalmology", icon="eye",
         name_ar="العيون", name_en="Ophthalmology",
         description_ar="فحص وعلاج مشكلات الرؤية وجراحات العيون الدقيقة.",
         description_en="Vision care, eye exams and precision ophthalmic surgery."),
]


def register_cli(app):
    @app.cli.command("seed-admin")
    def seed_admin():
        """ينشئ حساب مشرف افتراضي إن لم يكن موجودًا."""
        username = app.config["DEFAULT_ADMIN_USERNAME"]
        existing = Admin.query.filter_by(username=username).first()
        if existing:
            click.echo(f"الحساب '{username}' موجود مسبقًا.")
            return
        admin = Admin(username=username, full_name=app.config["DEFAULT_ADMIN_NAME"])
        admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        click.echo(f"تم إنشاء حساب المشرف '{username}' بنجاح.")

    @app.cli.command("seed-departments")
    def seed_departments():
        """يضيف الأقسام الطبية الافتراضية إن لم تكن موجودة."""
        added = 0
        for i, data in enumerate(DEFAULT_DEPARTMENTS):
            if Department.query.filter_by(slug=data["slug"]).first():
                continue
            dept = Department(order=i, **data)
            db.session.add(dept)
            added += 1
        db.session.commit()
        click.echo(f"تمت إضافة {added} قسم جديد.")

    @app.cli.command("init-db")
    def init_db():
        """ينشئ كل الجداول مباشرة (بديل سريع عن migrations للتجربة الأولى)."""
        db.create_all()
        click.echo("تم إنشاء جداول قاعدة البيانات.")
