"""
نقطة الدخول المطلوبة من أداة "Setup Python App" في cPanel (تعتمد على Passenger).
هذا الملف ضروري فقط عند النشر على استضافة تستخدم cPanel (مثل بيجوهوست عبر VPS/Cloud
مع دعم Python App). لا حاجة له عند النشر على Render.
"""
import sys
import os

# يضيف مجلد المشروع لمسار بايثون حتى يجد حزمة app
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

application = create_app()
