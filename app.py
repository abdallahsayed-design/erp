import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import base64
from io import BytesIO

# إعدادات الصفحة والشكل العام
st.set_page_config(page_title="نظام معرض الكبير لإدارة المخازن المتطور", layout="wide")

DB_FILE = "system_database.db"

# دالة للاتصال بقاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة
def init_sqlite_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    # إضافة مستخدمين افتراضيين إن لم يوجدوا
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?)", [
            ("admin", "123", "مدير"),
            ("sharaf", "456", "مشرف"),
            ("user1", "111", "موظف")
        ])
    
    # 2. جدول المخزن والأصناف
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            item_code TEXT PRIMARY KEY,
            item_name TEXT,
            category TEXT,
            unit_type TEXT,
            warehouse_loc TEXT,
            quantity INTEGER DEFAULT 0,
            purchase_price REAL DEFAULT 0.0,
            sale_price REAL DEFAULT 0.0
        )
    ''')
    
    # 3. جدول المبيعات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT,
            date TEXT,
            client_name TEXT,
            client_phone TEXT,
            client_address TEXT,
            sale_type TEXT,
            collect_system TEXT,
            collect_date TEXT,
            item_code TEXT,
            item_name TEXT,
            category TEXT,
            unit_type TEXT,
            warehouse_loc TEXT,
            quantity INTEGER,
            unit_price REAL,
            discount REAL,
            total_sale REAL,
            total_cost REAL,
            net_profit REAL,
            user_in_charge TEXT
        )
    ''')
    
    # 4. جدول المشتريات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT,
            date TEXT,
            vendor TEXT,
            item_code TEXT,
            item_name TEXT,
            category TEXT,
            unit_type TEXT,
            warehouse_loc TEXT,
            approved_purchase_price REAL,
            quantity INTEGER,
            total_purchase REAL,
            user_in_charge TEXT
        )
    ''')
    
    # 5. جدول المصاريف
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            details TEXT,
            amount REAL,
            user_in_charge TEXT
        )
    ''')
    
    # 6. جدول الحضور والانصراف
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT,
            date TEXT,
            check_in TEXT,
            check_out TEXT
        )
    ''')
    
    # 7. جدول جهات الاتصال
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_type TEXT,
            name TEXT,
            phone TEXT,
            address TEXT
        )
    ''')
    
    # 8. جدول الإعدادات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            showroom_name TEXT,
            address TEXT,
            support_number TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings VALUES (?, ?, ?)", 
                       ("معرض الكبير", "ابوحماد - قرية العراقي - بجوار مدرسة الشهيد صلاح فتحي", "0100XXXXXXX"))
        
    # 9. جدول الصلاحيات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            page_name TEXT PRIMARY KEY,
            admin_auth INTEGER,
            supervisor_auth INTEGER,
            employee_auth INTEGER
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM permissions")
    if cursor.fetchone()[0] == 0:
        all_pages = [
            "📦 إدارة الأصناف والمخزن", "📊 رصيد أول المدة Excel", "🔍 حالة المخزن", 
            "🤝 العملاء والموردين", "📥 حركة فواتير الشراء", "📤 حركة فواتير البيع", 
            "🔎 البحث عن الفواتير وطباعتها", "📈 تقارير البيع والشراء والأرباح", "💸 المصاريف", 
            "⏰ الحضور والانصراف", "⚙️ إدارة وتعديل الصلاحيات والحسابات", "⚙️ إعدادات بيانات الفاتورة والدعم"
        ]
        for page in all_pages:
            admin_p = 1
            super_p = 1 if page in ["🔍 حالة المخزن", "📥 حركة فواتير الشراء", "📤 حركة فواتير البيع", "🔎 البحث عن الفواتير وطباعتها", "⏰ الحضور والانصراف"] else 0
            emp_p = 1 if page in ["🔍 حالة المخزن", "📤 حركة فواتير البيع", "🔎 البحث عن الفواتير وطباعتها", "⏰ الحضور والانصراف"] else 0
            cursor.execute("INSERT INTO permissions VALUES (?, ?, ?, ?)", (page, admin_p, super_p, emp_p))

    conn.commit()
    conn.close()

init_sqlite_db()

# دالة مساعدة لجلب البيانات كـ DataFrame
def load_table(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# دالة مساعدة لتنفيذ أمر استعلام (إدخال/تعديل/حذف)
def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

# دالة تحويل الأرقام إلى كلمات عربية (التفقيط)
def number_to_arabic_words(number):
    try:
        num = int(float(number))
        if num == 0: return "صفر جنيهاً مصرياً لا غير"
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
        tens = ["", "عشرة", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        hundreds = ["", "مائة", "مائتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة", "سبعتامائة", "ثمانمائة", "تسعمائة"]
        words = []
        if num >= 1000:
            thousands = num // 1000
            if thousands == 1: words.append("ألف")
            elif thousands == 2: words.append("ألفين")
            elif 3 <= thousands <= 10: words.append(f"{units[thousands]} آلاف")
            else: words.append(f"{thousands} ألف")
            num %= 1000
        if num >= 100:
            words.append(hundreds[num // 100])
            num %= 100
        if num > 0:
            if len(words) > 0: words.append("و")
            if num < 10: words.append(units[num])
            elif num < 20:
                special = ["عشرة", "أحد عشر", "إثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
                words.append(special[num - 10])
            else:
                unit_part = num % 10
                tens_part = num // 10
                if unit_part > 0: words.append(f"{units[unit_part]} و{tens[tens_part]}")
                else: words.append(tens[tens_part])
        return "فقط " + " و ".join([w for w in words if w != "و"]) + " جنيهاً مصرياً لا غير"
    except: return ""

# جلب الإعدادات الحالية للبرنامج
settings_df = load_table("SELECT * FROM settings")
SHOWROOM_NAME = settings_df.iloc[0]["showroom_name"]
SHOWROOM_ADDRESS = settings_df.iloc
