#!/usr/bin/env bash
# نسخ احتياطي يومي لقاعدة بيانات Neon PostgreSQL باستخدام pg_dump
# الاستخدام: ضع هذا السكربت في cron يوميًا، مثال:
#   0 3 * * *  /path/to/medical_booking/scripts/backup_db.sh >> /var/log/medical_backup.log 2>&1
#
# ملاحظة: Neon يوفر أيضًا نسخًا احتياطية تلقائية ونقاط استرجاع زمنية
# (Point-in-Time Recovery) من لوحة تحكم المشروع مباشرة، وهذا السكربت
# يضيف طبقة نسخ احتياطي إضافية محلية/خارجية.

set -euo pipefail

# تحميل متغيرات البيئة
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/../backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
FILENAME="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

if [ -z "${DATABASE_URL_DIRECT:-}" ]; then
  echo "خطأ: DATABASE_URL_DIRECT غير معرّف في .env" >&2
  exit 1
fi

echo "جارٍ إنشاء نسخة احتياطية: $FILENAME"
pg_dump "$DATABASE_URL_DIRECT" | gzip > "$FILENAME"
echo "تم بنجاح."

# الاحتفاظ بآخر 14 نسخة فقط وحذف الأقدم
ls -1t "$BACKUP_DIR"/backup_*.sql.gz | tail -n +15 | xargs -r rm --
