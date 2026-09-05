from functools import wraps
from flask import session, current_app, abort
from flask_login import current_user
from app.models import Admin


def get_lang():
    lang = session.get("lang")
    if lang in current_app.config["LANGUAGES"]:
        return lang
    return current_app.config["DEFAULT_LANGUAGE"]


def get_dir():
    return "rtl" if get_lang() == "ar" else "ltr"


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped
