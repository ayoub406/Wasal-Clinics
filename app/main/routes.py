from flask import Blueprint, render_template
from app.models import Department

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    departments = Department.query.filter_by(is_active=True).order_by(Department.order).all()
    return render_template("index.html", departments=departments)


@main_bp.route("/departments")
def departments():
    departments = Department.query.filter_by(is_active=True).order_by(Department.order).all()
    return render_template("index.html", departments=departments, jump_to_departments=True)
