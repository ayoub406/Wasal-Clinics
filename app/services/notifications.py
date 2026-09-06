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


def send_whatsapp_template(to_phone: str, template_name: str, language_code: str, parameters: list) -> bool:
    """
    يرسل رسالة واتساب باستخدام قالب معتمد من Meta (Message Template).
    هذا هو الأسلوب المطلوب لإرسال إشعارات تبدأها العيادة (business-initiated)
    خارج نافذة الـ 24 ساعة، وهو ما ينطبق على تأكيد/رفض الحجوزات هنا.

    parameters: قائمة نصوص بترتيب المتغيرات {{1}} {{2}} {{3}}... داخل القالب.
    """
    if not to_phone:
        logger.warning("WhatsApp: لا يوجد رقم هاتف للإرسال إليه")
        return False

    clean_phone = "".join(ch for ch in to_phone if ch.isdigit())

    if not current_app.config.get("WHATSAPP_ENABLED"):
        logger.info(
            "[WhatsApp - وضع تجريبي - قالب %s] إلى %s: %s",
            template_name, clean_phone, parameters,
        )
        return True

    token = current_app.config.get("WHATSAPP_ACCESS_TOKEN")
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(p)} for p in parameters],
                }
            ],
        },
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(_graph_url(), json=payload, headers=headers, timeout=10)
        if response.status_code >= 400:
            logger.error("فشل إرسال قالب واتساب (%s): %s", response.status_code, response.text)
            return False
        return True
    except requests.RequestException as exc:
        logger.exception("خطأ أثناء الاتصال بواجهة واتساب: %s", exc)
        return False


def notify_admin_new_booking(appointment, lang="ar") -> bool:
    """
    يرسل تنبيه واتساب لرقم العيادة (ADMIN_NOTIFY_PHONE في متغيرات البيئة)
    بمجرد ما مريض يحجز موعد جديد. رسالة نصية حرة (مو قالب) لأنها تنبيه
    داخلي للعيادة نفسها، مو رسالة تسويقية للمريض.

    ملاحظة: لازم رقم العيادة يكون بدأ محادثة مع رقم واتساب العمل خلال
    آخر 24 ساعة حتى تصل الرسالة (قاعدة نافذة الخدمة عند Meta).
    """
    admin_phone = current_app.config.get("ADMIN_NOTIFY_PHONE")
    if not admin_phone:
        logger.info("ADMIN_NOTIFY_PHONE غير مضبوط - تخطي تنبيه العيادة")
        return False

    dept_name = appointment.department.name(lang) if appointment.department else ""
    doctor_name = appointment.doctor.name(lang) if appointment.doctor else ""
    when = f"{appointment.preferred_date} ({appointment.preferred_period})"

    if lang == "ar":
        period_ar = {"morning": "صباحًا", "evening": "مساءً"}.get(appointment.preferred_period, appointment.preferred_period)
        lines = [
            "📩 حجز موعد جديد",
            f"الاسم: {appointment.patient.full_name}",
            f"الهاتف: {appointment.patient.phone}",
            f"القسم: {dept_name}",
        ]
        if doctor_name:
            lines.append(f"الطبيب: {doctor_name}")
        lines.append(f"التاريخ المطلوب: {appointment.preferred_date} ({period_ar})")
        if appointment.notes:
            lines.append(f"ملاحظات المريض: {appointment.notes}")
        message = "\n".join(lines)
    else:
        lines = [
            "📩 New appointment booking",
            f"Name: {appointment.patient.full_name}",
            f"Phone: {appointment.patient.phone}",
            f"Department: {dept_name}",
        ]
        if doctor_name:
            lines.append(f"Doctor: {doctor_name}")
        lines.append(f"Requested: {when}")
        if appointment.notes:
            lines.append(f"Notes: {appointment.notes}")
        message = "\n".join(lines)

    return send_whatsapp_message(admin_phone, message)


def notify_appointment_confirmed(appointment, lang="ar") -> bool:
    """يرسل إشعار تأكيد الموعد. يستخدم القالب المعتمد إذا كان الإرسال الفعلي مفعّلًا،
    وإلا يطبع رسالة نصية مقروءة في السجل (وضع التطوير)."""
    dept_name = appointment.department.name(lang)
    when = appointment.confirmed_datetime.strftime("%Y-%m-%d %H:%M") if appointment.confirmed_datetime else ""

    if not current_app.config.get("WHATSAPP_ENABLED"):
        message = build_confirmation_message(appointment, lang=lang)
        return send_whatsapp_message(appointment.patient.phone, message)

    template_name = current_app.config.get("WHATSAPP_TEMPLATE_CONFIRM", "appointment_confirmed")
    template_lang = current_app.config.get("WHATSAPP_TEMPLATE_LANG", "ar")
    return send_whatsapp_template(
        appointment.patient.phone,
        template_name,
        template_lang,
        [appointment.patient.full_name, dept_name, when],
    )


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
