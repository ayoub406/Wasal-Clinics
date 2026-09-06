from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.extensions import db
from app.models import Department, Doctor, Patient, Appointment
from app.utils import get_lang
from app.services.notifications import notify_admin_new_booking

booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/book", methods=["GET", "POST"])
@booking_bp.route("/book/<slug>", methods=["GET", "POST"])
def book(slug=None):
    departments = Department.query.filter_by(is_active=True).order_by(Department.order).all()
    selected_department = None
    if slug:
        selected_department = Department.query.filter_by(slug=slug, is_active=True).first()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        department_id = request.form.get("department_id", type=int)
        doctor_id = request.form.get("doctor_id", type=int) or None
        preferred_date_raw = request.form.get("preferred_date", "")
        preferred_period = request.form.get("preferred_period", "morning")
        notes = request.form.get("notes", "").strip()

        errors = []
        if not full_name:
            errors.append("full_name")
        if not phone:
            errors.append("phone")
        if not department_id:
            errors.append("department_id")
        try:
            preferred_date = datetime.strptime(preferred_date_raw, "%Y-%m-%d").date()
            if preferred_date < date.today():
                errors.append("preferred_date")
        except ValueError:
            errors.append("preferred_date")

        if errors:
            flash("flash_booking_error", "error")
            return render_template(
                "book_appointment.html",
                departments=departments,
                selected_department=selected_department,
                form=request.form,
            )

        patient = Patient.query.filter_by(phone=phone).first()
        if not patient:
            patient = Patient(full_name=full_name, phone=phone, email=email or None)
            db.session.add(patient)
        else:
            patient.full_name = full_name
            if email:
                patient.email = email

        appointment = Appointment(
            patient=patient,
            department_id=department_id,
            doctor_id=doctor_id,
            preferred_date=preferred_date,
            preferred_period=preferred_period,
            notes=notes,
        )
        db.session.add(appointment)
        db.session.commit()

        # تنبيه فوري لرقم العيادة بمجرد ما مريض يحجز موعد جديد
        notify_admin_new_booking(appointment, lang="ar")

        session["last_booking_phone"] = phone
        return redirect(url_for("booking.success"))

    return render_template(
        "book_appointment.html",
        departments=departments,
        selected_department=selected_department,
        form={},
    )


@booking_bp.route("/success")
def success():
    return render_template("booking_success.html")


@booking_bp.route("/my-appointments", methods=["GET", "POST"])
def my_appointments():
    phone = request.values.get("phone", session.get("last_booking_phone", "")).strip()
    appointments = []
    searched = False
    if phone:
        searched = True
        patient = Patient.query.filter_by(phone=phone).first()
        if patient:
            appointments = (
                Appointment.query.filter_by(patient_id=patient.id)
                .order_by(Appointment.created_at.desc())
                .all()
            )
    return render_template(
        "my_appointments.html", appointments=appointments, phone=phone, searched=searched
    )


@booking_bp.route("/departments/<slug>/doctors")
def department_doctors(slug):
    """يعيد قائمة الأطباء لقسم معيّن (يُستخدم عبر JS عند تغيير القسم)."""
    from flask import jsonify

    department = Department.query.filter_by(slug=slug, is_active=True).first()
    if not department:
        return jsonify([])
    lang = get_lang()
    doctors = [
        {"id": d.id, "name": d.name(lang), "title": d.title(lang)}
        for d in department.doctors.filter_by(is_active=True).all()
    ]
    return jsonify(doctors)
