import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # قاعدة بيانات Neon PostgreSQL. تحويل postgres:// إلى postgresql:// إن لزم.
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "dev.db"))
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # إعدادات تجمّع الاتصالات (pool) لتحمّل عدد كبير من الزوار في نفس اللحظة
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.environ.get("DB_POOL_SIZE", 10)),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", 20)),
        "pool_recycle": 280,       # Neon يغلق الاتصالات الخاملة، نجدد الاتصال قبل ذلك
        "pool_pre_ping": True,     # يتحقق من صلاحية الاتصال قبل استخدامه
    }

    LANGUAGES = ["ar", "en"]
    DEFAULT_LANGUAGE = "ar"

    WHATSAPP_ENABLED = os.environ.get("WHATSAPP_ENABLED", "false").lower() == "true"
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v20.0")
    ADMIN_NOTIFY_PHONE = os.environ.get("ADMIN_NOTIFY_PHONE", "")

    DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")
    DEFAULT_ADMIN_NAME = os.environ.get("DEFAULT_ADMIN_NAME", "مدير النظام")

    BACKUP_DIR = os.environ.get("BACKUP_DIR", os.path.join(basedir, "backups"))
    DATABASE_URL_DIRECT = os.environ.get("DATABASE_URL_DIRECT", _db_url)

    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 30
