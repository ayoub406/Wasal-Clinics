from flask import Flask, session, request
from config import Config
from app.extensions import db, migrate, login_manager
from app.translations import translate
from app.utils import get_lang, get_dir
import logging

# بدون هذا الإعداد، رسائل logger.info() (زي رسائل واتساب التجريبية) ما
# تظهر إطلاقًا في سجلات Render، لأن الإعداد الافتراضي لبايثون يخفي أي
# رسالة أقل من مستوى WARNING إذا ما فيه معالج (handler) مضبوط مسبقًا.
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models import Patient, Admin

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("admin:"):
            return Admin.query.get(int(user_id.split(":")[1]))
        return Patient.query.get(int(user_id))

    # ------------------------------------------------------------------
    # Blueprints
    # ------------------------------------------------------------------
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.booking.routes import booking_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(booking_bp, url_prefix="/booking")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ------------------------------------------------------------------
    # اللغة والاتجاه متاحان في كل القوالب
    # ------------------------------------------------------------------
    @app.context_processor
    def inject_globals():
        return {
            "_": lambda key: translate(key, get_lang()),
            "current_lang": get_lang(),
            "current_dir": get_dir(),
        }

    @app.route("/set-language/<lang_code>")
    def set_language(lang_code):
        from flask import redirect, url_for
        if lang_code in app.config["LANGUAGES"]:
            session["lang"] = lang_code
        return redirect(request.referrer or url_for("main.index"))

    # ------------------------------------------------------------------
    # أوامر CLI مساعدة
    # ------------------------------------------------------------------
    from app.cli import register_cli
    register_cli(app)

    # ------------------------------------------------------------------
    # إنشاء الجداول وتهيئة البيانات الأولية تلقائيًا عند بدء التشغيل.
    # هذا يغني عن الحاجة لتشغيل أوامر flask يدويًا عبر Shell، وهو مفيد
    # خصوصًا على خطط الاستضافة المجانية (مثل Render Free) التي لا تتيح
    # الوصول لـ Shell. العملية آمنة ومتكررة (idempotent): لا تكرر الجداول
    # أو البيانات إذا كانت موجودة مسبقًا.
    # ------------------------------------------------------------------
    with app.app_context():
        try:
            from app.cli import DEFAULT_DEPARTMENTS
            from app.models import Department

            db.create_all()

            username = app.config["DEFAULT_ADMIN_USERNAME"]
            admin = Admin.query.filter_by(username=username).first()
            if not admin:
                admin = Admin(username=username, full_name=app.config["DEFAULT_ADMIN_NAME"])
                db.session.add(admin)
            # نزامن كلمة المرور مع متغير البيئة في كل مرة يشتغل الموقع،
            # هذا يضمن إن كلمة المرور الفعلية تطابق دائمًا المتغير المضبوط
            # في Render حتى لو تغيّر بعد إنشاء الحساب أول مرة.
            admin.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
            admin.full_name = app.config["DEFAULT_ADMIN_NAME"]

            for i, data in enumerate(DEFAULT_DEPARTMENTS):
                if not Department.query.filter_by(slug=data["slug"]).first():
                    db.session.add(Department(order=i, **data))

            db.session.commit()
        except Exception as exc:  # لا نوقف تشغيل التطبيق إذا فشلت التهيئة
            app.logger.warning(f"database bootstrap skipped/failed: {exc}")
            db.session.rollback()

    return app
