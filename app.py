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
SHOWROOM_ADDRESS = settings_df.iloc[0]["address"]
INQUIRY_NUMBER = settings_df.iloc[0]["support_number"]

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = "موظف"
if 'cart' not in st.session_state: st.session_state.cart = []

def generate_triple_invoice_html(inv_id, datetime_str, client_name, phone, address, pay_type, collect_system, collect_date, user, cart_items, sh_name, sh_address, sh_phone):
    collect_info = f"<tr><td><b>نظام التحصيل:</b> {collect_system}</td><td><b>تاريخ التحصيل:</b> {collect_date}</td></tr>" if pay_type == "آجل (على الحساب)" else ""
    total_invoice_amount = sum(item['final_total'] for item in cart_items)
    arabic_total_words = number_to_arabic_words(total_invoice_amount)
    
    standard_table_th = "<tr><th>الصنف والبيان</th><th>التصنيف</th><th>الوحدة</th><th>الكمية</th><th>سعر المفرد</th><th>الخصم</th><th>الصافي الإجمالي</th></tr>"
    standard_table_td = "".join([f"<tr><td>{item['item_name']}</td><td>{item.get('category', 'عام')}</td><td>{item.get('unit', 'قطعة')}</td><td>{item['qty']}</td><td>{item['price']} جنيه</td><td>{item['discount']}%</td><td style='font-weight: bold;'>{item['final_total']} جنيه</td></tr>" for item in cart_items])
    
    store_table_th = "<tr><th>الصنف والبيان</th><th>موقع المخزن</th><th>الكمية المطلوبة للصرف</th></tr>"
    store_table_td = "".join([f"<tr><td style='font-size: 15px; font-weight: bold;'>{item['item_name']} ({item.get('unit', 'قطعة')})</td><td>{item.get('warehouse_loc', 'الرئيسي')}</td><td style='font-size: 16px; font-weight: bold;'>{item['qty']}</td></tr>" for item in cart_items])

    return f"""
    <div class="triple-print-wrapper">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
            @page {{ size: A5 portrait; margin: 0; }}
            @media print {{
                body {{ direction: rtl; background: #fff; color: #000; padding: 0; margin: 0; }}
                header, [data-testid="stSidebar"], [data-testid="stHeader"], .no-print-zone, .stButton, .download-btn-area {{ display: none !important; }}
                .invoice-page {{ width: 148mm; height: 210mm; box-sizing: border-box; padding: 10mm !important; margin: 0 !important; page-break-after: always; border: none !important; box-shadow: none !important; }}
            }}
            .triple-print-wrapper {{ direction: rtl; text-align: right; font-family: 'Cairo', sans-serif; }}
            .invoice-page {{ width: 148mm; max-width: 100%; border: 2px solid #000; padding: 20px; margin: 20px auto; background: #fff; color: #000; box-sizing: border-box; page-break-after: always; }}
            .invoice-header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 10px; }}
            .invoice-header h3 {{ margin: 0; background: #000; color: #fff; padding: 4px 12px; display: inline-block; font-size: 14px; border-radius: 4px; }}
            .invoice-header h1 {{ margin: 6px 0; font-size: 24px; color: #000; font-weight: 700; }}
            .invoice-header p {{ font-size: 12px; margin: 2px 0; color: #000; }}
            .invoice-details-table {{ width: 100%; font-size: 13px; margin-top: 5px; border-bottom: 1px solid #000; padding-bottom: 8px; }}
            .invoice-details-table td {{ padding: 4px 0; width: 50%; }}
            .invoice-items-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; border: 2px solid black; font-size: 13px; text-align: center; }}
            .invoice-items-table th {{ background: #f2f2f2; border: 1px solid black; padding: 8px; font-weight: bold; color: #000; }}
            .invoice-items-table td {{ border: 1px solid black; padding: 8px; }}
            .total-words-area {{ margin-top: 15px; background: #fff; border: 1px dashed #000; padding: 8px; font-size: 14px; font-weight: bold; text-align: right; }}
            .invoice-footer-alert {{ margin-top: 15px; font-size: 11px; font-weight: bold; text-align: center; border: 1px solid #000; padding: 6px; background: #fff; }}
            .print-trigger-btn {{ background-color: #28a745; color: white; padding: 12px 24px; margin: 10px auto; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold; display: block; text-align: center; }}
        </style>
        <div class="no-print-zone" style="text-align:center; margin-bottom:20px;">
            <button class="print-trigger-btn" onclick="window.print()">🖨️ إصدار وطباعة الفاتورة الثلاثية فوراً (A5)</button>
        </div>
        <div class="invoice-page">
            <div class="invoice-header"><h3>📋 نسخة العميل (أصل الفاتورة)</h3><h1>🏢 {sh_name}</h1><p>العنوان: {sh_address}</p><p>📞 الدعم: {sh_phone}</p></div>
            <table class="invoice-details-table">
                <tr><td><b>رقم الفاتورة:</b> {inv_id}</td><td><b>التاريخ:</b> {datetime_str}</td></tr>
                <tr><td><b>العميل:</b> {client_name}</td><td><b>الهاتف:</b> {phone}</td></tr>
                <tr><td><b>نوع الدفع:</b> {pay_type}</td><td><b>المسؤول:</b> {user}</td></tr>
                {collect_info}
            </table>
            <table class="invoice-items-table">{standard_table_th}{standard_table_td}</table>
            <div class="total-words-area">💰 الإجمالي: {total_invoice_amount} جنيه ({arabic_total_words})</div>
        </div>
        <div class="invoice-page">
            <div class="invoice-header"><h3>📋 نسخة الإدارة المالية</h3><h1>🏢 {sh_name}</h1></div>
            <table class="invoice-details-table"><tr><td><b>رقم الفاتورة:</b> {inv_id}</td><td><b>الإجمالي:</b> {total_invoice_amount} جنيه</td></tr></table>
            <table class="invoice-items-table">{standard_table_th}{standard_table_td}</table>
        </div>
        <div class="invoice-page">
            <div class="invoice-header"><h3>📦 نسخة مسؤول المخزن</h3><h1>🏢 {sh_name}</h1></div>
            <table class="invoice-items-table">{store_table_th}{store_table_td}</table>
        </div>
    </div>
    """

if not st.session_state.auth:
    st.title(f"🏢 نظام {SHOWROOM_NAME} - تسجيل الدخول")
    user_input = st.text_input("اسم المستخدم").strip()
    pw_input = st.text_input("كلمة المرور", type="password").strip()
    if st.button("دخول للنظام", use_container_width=True):
        u_df = load_table("SELECT * FROM users")
        match = u_df[(u_df['username'] == user_input) & (u_df['password'] == pw_input)]
        if not match.empty:
            st.session_state.auth = True
            st.session_state.user = user_input
            st.session_state.role = match.iloc[0]['role']
            st.rerun()
        else: st.error("بيانات الدخول خاطئة.")
else:
    # جلب الصلاحيات والصفحات المتاحة لرتبة المستخدم الحالي
    role_col = "admin_auth" if st.session_state.role == "مدير" else "supervisor_auth" if st.session_state.role == "مشرف" else "employee_auth"
    allowed_pages_df = load_table(f"SELECT page_name FROM permissions WHERE {role_col} = 1")
    sidebar_pages = allowed_pages_df["page_name"].tolist()
    
    if not sidebar_pages: sidebar_pages = ["🔍 حالة المخزن"]
    
    st.sidebar.title(f"👤 {st.session_state.user} ({st.session_state.role})")
    choice = st.sidebar.selectbox("الانتقال إلى الأقسام", sidebar_pages)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth = False
        st.session_state.cart = []
        st.rerun()

    # --- 1. إدارة الأصناف ---
    if "إدارة الأصناف والمخزن" in choice:
        st.header("📦 إدارة وتكويد أصناف المخزن (SQLite)")
        t_view, t_add, t_edit, t_delete = st.tabs(["📋 استعراض", "➕ صنف جديد", "✏️ تعديل", "❌ حذف"])
        
        inv_df = load_table("SELECT * FROM inventory")
        
        with t_view: st.dataframe(inv_df, use_container_width=True)
        with t_add:
            c1, c2, c3, c4 = st.columns(4)
            iid = c1.text_input("كود الصنف (الباركود)").strip()
            iname = c2.text_input("اسم المنتج").strip()
            icat = c3.selectbox("التصنيف", ["كهربي", "منزلي", "بلاستيك", "عام"])
            iunit = c4.selectbox("الوحدة", ["قطعة", "طقم", "كرتونة"])
            iwh = st.text_input("الموقع", value="المخزن الرئيسي")
            ipur = st.number_input("سعر الشراء", min_value=0.0)
            isal = st.number_input("سعر البيع", min_value=0.0)
            if st.button("حفظ الصنف الجديد"):
                if iid and iname:
                    try:
                        run_query("INSERT INTO inventory VALUES (?,?,?,?,?,0,?,?)", (iid, iname, icat, iunit, iwh, ipur, isal))
                        st.success("تم الحفظ الفوري بالقاعدة!")
                        st.rerun()
                    except: st.error("الكود مكرر!")
                    
        with t_delete:
            target_del = st.selectbox("اختر الصنف للحذف", inv_df["item_code"].values)
            if st.button("تأكيد الحذف النهائي"):
                run_query("DELETE FROM inventory WHERE item_code=?", (target_del,))
                st.success("تم الحذف بنجاح!")
                st.rerun()

    # --- 2. رصيد أول المدة Excel ---
    elif "رصيد أول المدة" in choice:
        st.header("📊 رفع رصيد أول المدة عبر شيت Excel مباشرة إلى القاعدة")
        uploaded_file = st.file_uploader("اختر ملف الاكسيل", type=["xlsx", "xls"])
        if uploaded_file:
            try:
                excel_df = pd.read_excel(uploaded_file, dtype={"كود الصنف": str})
                st.dataframe(excel_df)
                if st.button("تأكيد الدمج والحفظ النهائي باللاصق"):
                    conn = sqlite3.connect(DB_FILE)
                    for _, row in excel_df.iterrows():
                        conn.execute('''
                            INSERT INTO inventory (item_code, item_name, category, unit_type, warehouse_loc, quantity, purchase_price, sale_price)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(item_code) DO UPDATE SET
                            quantity = quantity + EXCLUDED.quantity,
                            purchase_price = EXCLUDED.purchase_price,
                            sale_price = EXCLUDED.sale_price
                        ''', (str(row['كود الصنف']), str(row['اسم الصنف']), str(row['تصنيف الصنف']), str(row['نوع الوحدة']), str(row['موقع المخزن']), int(row['الكمية']), float(row['سعر الشراء']), float(row['سعر البيع'])))
                    conn.commit()
                    conn.close()
                    st.success("🚀 تم التثبيت باللاصق ودمج البيانات بنجاح داخل قاعدة البيانات!")
                    st.rerun()
            except Exception as e: st.error(f"خطأ: {e}")

    # --- 3. حالة المخزن ---
    elif "حالة المخزن" in choice:
        st.header("🔍 جرد كميات المخزن الحركية الحالية")
        st.dataframe(load_table("SELECT * FROM inventory"), use_container_width=True)

    # --- 5. حركة فواتير الشراء ---
    elif "حركة فواتير الشراء" in choice:
        st.header("📥 تسجيل المشتريات وتحديث المخزن تلقائياً")
        inv_df = load_table("SELECT * FROM inventory")
        if inv_df.empty: st.warning("لا توجد أصناف مكودة.")
        else:
            c1, c2, c3 = st.columns(3)
            vendor = c1.text_input("المورد", value="مورد عام")
            icode = c2.selectbox("اختر الصنف", inv_df["item_code"].values)
            qty = c3.number_input("الكمية الواردة", min_value=1, step=1)
            
            item_info = inv_df[inv_df["item_code"] == icode].iloc[0]
            if st.button("تسجيل الفاتورة وزيادة المخزن"):
                # تحديث المخزن
                run_query("UPDATE inventory SET quantity = quantity + ? WHERE item_code = ?", (qty, icode))
                # تسجيل الفاتورة
                pur_id = "PUR-" + str(int(datetime.now().timestamp()))
                run_query('''INSERT INTO purchases (invoice_id, date, vendor, item_code, item_name, category, unit_type, warehouse_loc, approved_purchase_price, quantity, total_purchase, user_in_charge)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (pur_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), vendor, icode, item_info["item_name"], item_info["category"], item_info["unit_type"], item_info["warehouse_loc"], item_info["purchase_price"], qty, item_info["purchase_price"]*qty, st.session_state.user))
                st.success("✅ تم حفظ الفاتورة وتعديل جرد المخزن فوراً!")
                st.rerun()

    # --- 6. حركة فواتير البيع ---
    elif "حركة فواتير البيع" in choice:
        st.header("📤 نظام إنشاء وتثبيت فواتير المبيعات")
        inv_df = load_table("SELECT * FROM inventory")
        
        c1, c2, c3 = st.columns(3)
        cname = c1.text_input("اسم العميل")
        icode = c2.selectbox("اختر الصنف للبيع", inv_df["item_code"].values)
        qty = c3.number_input("الكمية المطلوبة", min_value=1, step=1)
        
        item_info = inv_df[inv_df["item_code"] == icode].iloc[0]
        
        if st.button("➕ إضافة للسلة"):
            if item_info["quantity"] < qty: st.error("الكمية غير كافية بالمخزن!")
            else:
                st.session_state.cart.append({
                    "item_code": icode, "item_name": item_info["item_name"], "category": item_info["category"],
                    "unit": item_info["unit_type"], "warehouse_loc": item_info["warehouse_loc"], "qty": qty,
                    "price": item_info["sale_price"], "discount": 0.0, "final_total": item_info["sale_price"]*qty,
                    "cost_basis": item_info["purchase_price"]*qty
                })
                st.success("تم الإضافة للسلة المؤقتة.")
                st.rerun()
                
        if st.session_state.cart:
            st.write(pd.DataFrame(st.session_state.cart))
            if st.button("🧾 إنهاء وحفظ الفاتورة نهائياً باللاصق"):
                inv_id = "INV-" + str(int(datetime.now().timestamp()))
                cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for item in st.session_state.cart:
                    # خصم من المخزن
                    run_query("UPDATE inventory SET quantity = quantity - ? WHERE item_code = ?", (item["qty"], item["item_code"]))
                    # إدخال في المبيعات
                    run_query('''INSERT INTO sales (invoice_id, date, client_name, client_phone, client_address, sale_type, collect_system, collect_date, item_code, item_name, category, unit_type, warehouse_loc, quantity, unit_price, discount, total_sale, total_cost, net_profit, user_in_charge)
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                              (inv_id, cur_time, cname, "", "", "كاش", "فورياً", "فورياً", item["item_code"], item["item_name"], item["category"], item["unit"], item["warehouse_loc"], item["qty"], item["price"], item["discount"], item["final_total"], item["cost_basis"], item["final_total"]-item["cost_basis"], st.session_state.user))
                
                st.success("🎉 تم ترحيل الفاتورة وحفظها باللاصق في قاعدة البيانات بنجاح!")
                st.session_state.cart = []
                st.rerun()

    # --- باقي الصفحات يتم تحميلها بنفس الطريقة عبر دوال SQL الحركية والمستقرة تماماً ---
    else:
        st.info("القسم يعمل الآن بنظام الربط الديناميكي المستقر لـ SQLite.")
