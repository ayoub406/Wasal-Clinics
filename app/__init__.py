from flask import Flask, session, request
from config import Config
from app.extensions import db, migrate, login_manager
from app.translations import translate
from app.utils import get_lang, get_dir


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

    return app
