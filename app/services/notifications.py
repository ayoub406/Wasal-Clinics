"""
خدمة إرسال إشعارات واتساب للمرضى عبر Meta WhatsApp Cloud API.

للتفعيل:
1. أنشئ تطبيق واتساب على Meta for Developers.
2. احصل على WHATSAPP_PHONE_NUMBER_ID و WHATSAPP_ACCESS_TOKEN.
3. ضع القيم في ملف .env وفعّل WHATSAPP_ENABLED=true

في حال عدم التفعيل، تُطبع الرسالة في السجل (console) فقط - مفيد أثناء التطوير.
"""

import logging
import requests
from flask import current_app

logger = logging.getLogger("whatsapp")


def _graph_url():
    version = current_app.config.get("WHATSAPP_API_VERSION", "v20.0")
    phone_id = current_app.config.get("WHATSAPP_PHONE_NUMBER_ID")
    return f"https://graph.facebook.com/{version}/{phone_id}/messages"


def send_whatsapp_message(to_phone: str, message: str) -> bool:
    """يرسل رسالة نصية واتساب لرقم هاتف بصيغة دولية (مثال: 218912345678)."""

    if not to_phone:
        logger.warning("WhatsApp: لا يوجد رقم هاتف للإرسال إليه")
        return False

    clean_phone = "".join(ch for ch in to_phone if ch.isdigit())

    if not current_app.config.get("WHATSAPP_ENABLED"):
        logger.info("[WhatsApp - وضع تجريبي] إلى %s:\n%s", clean_phone, message)
        return True

    token = current_app.config.get("WHATSAPP_ACCESS_TOKEN")
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "text",
        "text": {"body": message, "preview_url": False},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(_graph_url(), json=payload, headers=headers, timeout=10)
        if response.status_code >= 400:
            logger.error("فشل إرسال واتساب (%s): %s", response.status_code, response.text)
            return False
        return True
    except requests.RequestException as exc:
        logger.exception("خطأ أثناء الاتصال بواجهة واتساب: %s", exc)
        return False


def build_confirmation_message(appointment, lang="ar"):
    dept_name = appointment.department.name(lang)
    doctor_name = appointment.doctor.name(lang) if appointment.doctor else ""
    when = appointment.confirmed_datetime.strftime("%Y-%m-%d %H:%M") if appointment.confirmed_datetime else ""

    if lang == "ar":
        lines = [
            f"مرحبًا {appointment.patient.full_name} 👋",
            f"تم تأكيد موعدك في قسم {dept_name}.",
        ]
        if doctor_name:
            lines.append(f"مع الطبيب: {doctor_name}")
        lines.append(f"الموعد: {when}")
        if appointment.admin_note:
            lines.append(f"ملاحظة: {appointment.admin_note}")
        lines.append("نتمنى لك دوام الصحة والعافية 🌿")
        return "\n".join(lines)

    lines = [
        f"Hello {appointment.patient.full_name} 👋",
        f"Your appointment in {dept_name} has been confirmed.",
    ]
    if doctor_name:
        lines.append(f"With: {doctor_name}")
    lines.append(f"Date & time: {when}")
    if appointment.admin_note:
        lines.append(f"Note: {appointment.admin_note}")
    lines.append("Wishing you good health 🌿")
    return "\n".join(lines)


def build_rejection_message(appointment, lang="ar"):
    dept_name = appointment.department.name(lang)
    if lang == "ar":
        msg = f"مرحبًا {appointment.patient.full_name}، نعتذر عن عدم إمكانية تأكيد طلب الحجز في قسم {dept_name} بالموعد المطلوب."
        if appointment.admin_note:
            msg += f"\nملاحظة: {appointment.admin_note}"
        msg += "\nيمكنكم إعادة الحجز بموعد آخر عبر الموقع."
        return msg

    msg = f"Hello {appointment.patient.full_name}, unfortunately we couldn't confirm your booking in {dept_name} for the requested time."
    if appointment.admin_note:
        msg += f"\nNote: {appointment.admin_note}"
    msg += "\nYou're welcome to book another available slot on our website."
    return msg
