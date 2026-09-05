from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    name_ar = db.Column(db.String(120), nullable=False)
    name_en = db.Column(db.String(120), nullable=False)
    description_ar = db.Column(db.Text, default="")
    description_en = db.Column(db.Text, default="")
    icon = db.Column(db.String(40), default="stethoscope")   # اسم أيقونة SVG
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)

    doctors = db.relationship("Doctor", backref="department", lazy="dynamic")
    appointments = db.relationship("Appointment", backref="department", lazy="dynamic")

    def name(self, lang):
        return self.name_ar if lang == "ar" else self.name_en

    def description(self, lang):
        return self.description_ar if lang == "ar" else self.description_en


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    full_name_ar = db.Column(db.String(150), nullable=False)
    full_name_en = db.Column(db.String(150), nullable=False)
    title_ar = db.Column(db.String(150), default="")
    title_en = db.Column(db.String(150), default="")
    photo_url = db.Column(db.String(300), default="")
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship("Appointment", backref="doctor", lazy="dynamic")

    def name(self, lang):
        return self.full_name_ar if lang == "ar" else self.full_name_en

    def title(self, lang):
        return self.title_ar if lang == "ar" else self.title_en


class Patient(UserMixin, db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False, index=True)
    email = db.Column(db.String(150), nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="patient", lazy="dynamic")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(150), default="")
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def get_id(self):
        # نضيف بادئة لتمييز جلسة المشرف عن جلسة المريض في نفس نظام Flask-Login
        return f"admin:{self.id}"


STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_CANCELLED = "cancelled"
STATUS_COMPLETED = "completed"

PERIOD_MORNING = "morning"
PERIOD_EVENING = "evening"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=True)

    preferred_date = db.Column(db.Date, nullable=False)
    preferred_period = db.Column(db.String(20), default=PERIOD_MORNING)
    notes = db.Column(db.Text, default="")

    confirmed_datetime = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default=STATUS_PENDING, index=True)
    admin_note = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def status_label(self, lang):
        labels = {
            "ar": {
                STATUS_PENDING: "قيد المراجعة",
                STATUS_APPROVED: "مؤكد",
                STATUS_REJECTED: "مرفوض",
                STATUS_CANCELLED: "ملغى",
                STATUS_COMPLETED: "مكتمل",
            },
            "en": {
                STATUS_PENDING: "Pending review",
                STATUS_APPROVED: "Confirmed",
                STATUS_REJECTED: "Declined",
                STATUS_CANCELLED: "Cancelled",
                STATUS_COMPLETED: "Completed",
            },
        }
        return labels[lang].get(self.status, self.status)
