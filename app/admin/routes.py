from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Appointment, Department, Doctor, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
from app.utils import admin_required, get_lang
from app.services.notifications import (
    send_whatsapp_message,
    build_confirmation_message,
    build_rejection_message,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    status_filter = request.args.get("status", "all")
    query = Appointment.query.order_by(Appointment.created_at.desc())
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    appointments = query.all()

    counts = {
        "all": Appointment.query.count(),
        "pending": Appointment.query.filter_by(status=STATUS_PENDING).count(),
        "approved": Appointment.query.filter_by(status=STATUS_APPROVED).count(),
        "rejected": Appointment.query.filter_by(status=STATUS_REJECTED).count(),
    }

    return render_template(
        "admin/dashboard.html",
        appointments=appointments,
        counts=counts,
        status_filter=status_filter,
    )


@admin_bp.route("/appointments/<int:appointment_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    confirmed_raw = request.form.get("confirmed_datetime")
    admin_note = request.form.get("admin_note", "").strip()

    try:
        appointment.confirmed_datetime = datetime.strptime(confirmed_raw, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        flash("flash_booking_error", "error")
        return redirect(url_for("admin.dashboard"))

    appointment.status = STATUS_APPROVED
    appointment.admin_note = admin_note
    db.session.commit()

    # إرسال إشعار واتساب للمريض بلغته المفضلة (نستخدم العربية افتراضيًا)
    message = build_confirmation_message(appointment, lang="ar")
    send_whatsapp_message(appointment.patient.phone, message)

    flash("flash_appointment_approved", "success")
    return redirect(url_for("admin.dashboard", status=request.form.get("return_filter", "all")))


@admin_bp.route("/appointments/<int:appointment_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    admin_note = request.form.get("admin_note", "").strip()

    appointment.status = STATUS_REJECTED
    appointment.admin_note = admin_note
    db.session.commit()

    message = build_rejection_message(appointment, lang="ar")
    send_whatsapp_message(appointment.patient.phone, message)

    flash("flash_appointment_rejected", "success")
    return redirect(url_for("admin.dashboard", status=request.form.get("return_filter", "all")))


# --------------------------------------------------------------------
# إدارة الأقسام والأطباء
# --------------------------------------------------------------------

@admin_bp.route("/departments", methods=["GET", "POST"])
@login_required
@admin_required
def departments():
    if request.method == "POST":
        dept = Department(
            slug=request.form.get("slug", "").strip(),
            name_ar=request.form.get("name_ar", "").strip(),
            name_en=request.form.get("name_en", "").strip(),
            description_ar=request.form.get("description_ar", "").strip(),
            description_en=request.form.get("description_en", "").strip(),
            icon=request.form.get("icon", "stethoscope").strip(),
            order=Department.query.count(),
        )
        db.session.add(dept)
        db.session.commit()
        return redirect(url_for("admin.departments"))

    all_departments = Department.query.order_by(Department.order).all()
    return render_template("admin/departments.html", departments=all_departments)


@admin_bp.route("/departments/<int:department_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_department(department_id):
    dept = Department.query.get_or_404(department_id)
    dept.is_active = not dept.is_active
    db.session.commit()
    return redirect(url_for("admin.departments"))


@admin_bp.route("/doctors", methods=["GET", "POST"])
@login_required
@admin_required
def doctors():
    if request.method == "POST":
        doctor = Doctor(
            department_id=request.form.get("department_id", type=int),
            full_name_ar=request.form.get("full_name_ar", "").strip(),
            full_name_en=request.form.get("full_name_en", "").strip(),
            title_ar=request.form.get("title_ar", "").strip(),
            title_en=request.form.get("title_en", "").strip(),
        )
        db.session.add(doctor)
        db.session.commit()
        return redirect(url_for("admin.doctors"))

    all_doctors = Doctor.query.order_by(Doctor.id.desc()).all()
    all_departments = Department.query.order_by(Department.order).all()
    return render_template("admin/doctors.html", doctors=all_doctors, departments=all_departments)
