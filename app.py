import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64
from io import BytesIO
from io import StringIO

# إعدادات الصفحة والشكل العام
st.set_page_config(page_title="نظام معرض الكبير لإدارة المخازن المتطور", layout="wide")

# أسماء ملفات البيانات (CSV المعتمدة في مشروعك)
INVENTORY_FILE = "inventory_data.csv"
USERS_FILE = "users_data.csv"
SALES_FILE = "sales_data.csv"
PURCHASES_FILE = "purchases_data.csv"
EXPENSES_FILE = "expenses_data.csv"
ATTENDANCE_FILE = "attendance_data.csv"
CONTACTS_FILE = "contacts_data.csv"
PERMISSIONS_FILE = "permissions_config.csv"
SETTINGS_FILE = "system_settings.csv"
RETURNS_FILE = "returns_data.csv"  # ملف المردودات الجديد

# دالة تحويل الأرقام إلى كلمات عربية (التفقيط)
def number_to_arabic_words(number):
    try:
        num = int(float(number))
        if num == 0: return "صفر جنيهاً مصرياً لا غير"
        
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
        tens = ["", "عشرة", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        hundreds = ["", "مائة", "مائتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة", "سبعون", "ثمانمائة", "تسعمائة"]
        
        words = []
        if num >= 1000:
            thousands = num // 1000
            if thousands == 1: words.append("ألف")
            elif thousands == 2: words.append("ألفين")
            elif thousands >= 3 and thousands <= 10: words.append(f"{units[thousands]} آلاف")
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
                if unit_part > 0:
                    words.append(f"{units[unit_part]} و{tens[tens_part]}")
                else:
                    words.append(tens[tens_part])
                    
        return "فقط " + " و ".join([w for w in words if w != "و"]) + " جنيهاً مصرياً لا غير"
    except:
        return ""

# دالة تهيئة الملفات وإنشائها في حال عدم وجودها
def init_files():
    if not os.path.exists(USERS_FILE):
        pd.DataFrame([
            {"username": "admin", "password": "123", "role": "مدير"},
            {"username": "sharaf", "password": "456", "role": "مشرف"},
            {"username": "user1", "password": "111", "role": "موظف"}
        ]).to_csv(USERS_FILE, index=False, encoding='utf-8-sig')
        
    if not os.path.exists(INVENTORY_FILE):
        pd.DataFrame(columns=["كود الصنف", "اسم الصنف", "تصنيف الصنف", "نوع الوحدة", "موقع المخزن", "الكمية", "سعر الشراء", "سعر البيع"]).to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
        
    if not os.path.exists(SALES_FILE):
        pd.DataFrame(columns=["رقم الفاتورة", "التاريخ", "اسم العميل", "هاتف العميل", "العنوان", "نوع البيع", "نظام التحصيل", "تاريخ التحصيل", "كود الصنف", "الصنف", "تصنيف الصنف", "نوع الوحدة", "موقع المخزن", "الكمية", "سعر الوحدة", "الخصم %", "إجمالي البيع", "تكلفة الشراء الإجمالية", "صافي ربح الفاتورة", "المسؤول"]).to_csv(SALES_FILE, index=False, encoding='utf-8-sig')
        
    if not os.path.exists(RETURNS_FILE):
        pd.DataFrame(columns=["رقم الإرجاع", "رقم الفاتورة الأصلية", "التاريخ", "اسم العميل", "كود الصنف", "الصنف", "الكمية المرجعة", "المبلغ المردود", "المسؤول"]).to_csv(RETURNS_FILE, index=False, encoding='utf-8-sig')

    if not os.path.exists(PURCHASES_FILE):
        pd.DataFrame(columns=["رقم الفاتورة", "التاريخ", "المورد", "كود الصنف", "الصنف", "تصنيف الصنف", "نوع الوحدة", "موقع المخزن", "سعر الشراء المعتمد", "الكمية", "إجمالي الشراء", "المسؤول"]).to_csv(PURCHASES_FILE, index=False, encoding='utf-8-sig')
        
    if not os.path.exists(EXPENSES_FILE):
        pd.DataFrame(columns=["التاريخ", "البيان", "المبلغ", "المسؤول"]).to_csv(EXPENSES_FILE, index=False, encoding='utf-8-sig')
        
    if not os.path.exists(ATTENDANCE_FILE):
        pd.DataFrame(columns=["الموظف", "التاريخ", "وقت الحضور", "وقت الانصراف"]).to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')
        
    if not os.path.exists(CONTACTS_FILE):
        pd.DataFrame(columns=["النوع", "الاسم", "الهاتف", "العنوان"]).to_csv(CONTACTS_FILE, index=False, encoding='utf-8-sig')
    
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame([{"اسم المعرض": "معرض الكبير", "العنوان": "ابوحماد - قرية العراقي - بجوار مدرسة الشهيد صلاح فتحي", "رقم الدعم": "0100XXXXXXX"}]).to_csv(SETTINGS_FILE, index=False, encoding='utf-8-sig')

    all_pages = [
        "📦 إدارة الأصناف والمخزن", "📊 رصيد أول المدة Excel", "🔍 حالة المخزن", 
        "🤝 العملاء والموردين", "📥 حركة فواتير الشراء", "📤 حركة فواتير البيع", 
        "↩️ ارتجاع فواتير البيع", "🔎 البحث عن الفواتير وطباعتها", "📈 تقارير البيع والشراء والأرباح", "💸 المصاريف", 
        "⏰ الحضور والانصراف", "⚙️ إدارة وتعديل الصلاحيات والحسابات", "⚙️ إعدادات بيانات الفاتورة والدعم"
    ]
    
    if not os.path.exists(PERMISSIONS_FILE):
        default_perms = []
        for page in all_pages:
            default_perms.append({
                "اسم الصفحة": page, 
                "مدير": True, 
                "مشرف": True if page in ["🔍 حالة المخزن", "📥 حركة فواتير الشراء", "📤 حركة فواتير البيع", "↩️ ارتجاع فواتير البيع", "🔎 البحث عن الفواتير وطباعتها", "⏰ الحضور والانصراف"] else False, 
                "موظف": True if page in ["🔍 حالة المخزن", "📤 حركة فواتير البيع", "↩️ ارتجاع فواتير البيع", "🔎 البحث عن الفواتير وطباعتها", "⏰ الحضور والانصراف"] else False
            })
        pd.DataFrame(default_perms).to_csv(PERMISSIONS_FILE, index=False, encoding='utf-8-sig')

init_files()

# دالة لتحميل جميع البيانات في الـ Session State
def load_data_into_session():
    if 'data_loaded' not in st.session_state or st.sidebar.button("🔄 تحديث شامل للبيانات", key="global_refresh"):
        st.session_state.inv_df = pd.read_csv(INVENTORY_FILE, dtype={"كود الصنف": str})
        for col in ["تصنيف الصنف", "نوع الوحدة", "موقع المخزن"]:
            if col not in st.session_state.inv_df.columns:
                st.session_state.inv_df[col] = "غير محدد"
                
        st.session_state.inv_df["الكمية"] = pd.to_numeric(st.session_state.inv_df["الكمية"], errors='coerce').fillna(0).astype(int)
        st.session_state.inv_df["سعر الشراء"] = pd.to_numeric(st.session_state.inv_df["سعر الشراء"], errors='coerce').fillna(0.0)
        st.session_state.inv_df["سعر البيع"] = pd.to_numeric(st.session_state.inv_df["سعر البيع"], errors='coerce').fillna(0.0)

        st.session_state.sales_df = pd.read_csv(SALES_FILE, dtype={"رقم الفاتورة": str, "كود الصنف": str})
        st.session_state.returns_df = pd.read_csv(RETURNS_FILE, dtype={"رقم الإرجاع": str, "رقم الفاتورة الأصلية": str, "كود الصنف": str})
        st.session_state.purchases_df = pd.read_csv(PURCHASES_FILE, dtype={"رقم الفاتورة": str, "كود الصنف": str})
        st.session_state.exp_df = pd.read_csv(EXPENSES_FILE)
        st.session_state.att_df = pd.read_csv(ATTENDANCE_FILE)
        st.session_state.contacts_df = pd.read_csv(CONTACTS_FILE, dtype=str)
        st.session_state.data_loaded = True

load_data_into_session()

settings_df = pd.read_csv(SETTINGS_FILE)
SHOWROOM_NAME = settings_df.iloc[0]["اسم المعرض"]
SHOWROOM_ADDRESS = settings_df.iloc[0]["العنوان"]
INQUIRY_NUMBER = settings_df.iloc[0]["رقم الدعم"]

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = "موظف"
if 'cart' not in st.session_state: st.session_state.cart = []

def generate_triple_invoice_html(inv_id, datetime_str, client_name, phone, address, pay_type, collect_system, collect_date, user, cart_items, sh_name, sh_address, sh_phone):
    collect_info = f"<tr><td><b>نظام التحصيل:</b> {collect_system}</td><td><b>تاريخ التحصيل:</b> {collect_date}</td></tr>" if pay_type == "آجل (على الحساب)" else ""
    
    total_invoice_amount = sum(item['final_total'] for item in cart_items)
    arabic_total_words = number_to_arabic_words(total_invoice_amount)
    
    standard_table_th = "<tr><th>الصنف والبيان</th><th>التصنيف</th><th>الوحدة</th><th>الكمية</th><th>سعر المفرد</th><th>الخصم</th><th>الصافي الإجمالي</th></tr>"
    standard_table_td = ""
    for item in cart_items:
        standard_table_td += f"<tr><td>{item['item_name']}</td><td>{item.get('category', 'عام')}</td><td>{item.get('unit', 'قطعة')}</td><td>{item['qty']}</td><td>{item['price']} جنيه</td><td>{item['discount']}%</td><td style='font-weight: bold;'>{item['final_total']} جنيه</td></tr>"
    
    store_table_th = "<tr><th>الصنف والبيان</th><th>موقع المخزن</th><th>الكمية المطلوبة للصرف</th></tr>"
    store_table_td = ""
    for item in cart_items:
        store_table_td += f"<tr><td style='font-size: 15px; font-weight: bold;'>{item['item_name']} ({item.get('unit', 'قطعة')})</td><td>{item.get('warehouse_loc', 'الرئيسي')}</td><td style='font-size: 16px; font-weight: bold;'>{item['qty']}</td></tr>"

    html_content = f"""
    <div class="triple-print-wrapper">
        <style>
            @page {{ size: A5 portrait; margin: 0; }}
            @media print {{
                body {{ direction: rtl; background: #fff; color: #000; padding: 0; margin: 0; }}
                header, [data-testid="stSidebar"], [data-testid="stHeader"], .no-print-zone, .stButton, .download-btn-area {{ display: none !important; }}
                .invoice-page {{ width: 148mm; height: 210mm; box-sizing: border-box; padding: 10mm !important; margin: 0 !important; page-break-after: always; border: none !important; box-shadow: none !important; }}
            }}
            .triple-print-wrapper {{ direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Arial, sans-serif; }}
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
            <div class="invoice-header">
                <h3>📋 نسخة العميل (أصل الفاتورة)</h3>
                <h1>🏢 {sh_name}</h1>
                <p>العنوان: {sh_address}</p>
                <p style="font-size: 12px; font-weight: bold;">📞 رقم الاستعلام والدعم: {sh_phone}</p>
            </div>
            <table class="invoice-details-table">
                <tr><td><b>رقم الفاتورة:</b> {inv_id}</td><td><b>التاريخ والوقت:</b> {datetime_str}</td></tr>
                <tr><td><b>اسم العميل:</b> {client_name}</td><td><b>الهاتف:</b> {phone if phone else 'غير محدد'}</td></tr>
                <tr><td><b>العنوان:</b> {address if address else 'غير محدد'}</td><td><b>المسؤول:</b> {user}</td></tr>
                <tr><td><b>نوع الدفع:</b> {pay_type}</td><td><b>الإجمالي الكلي:</b> {total_invoice_amount} جنيه</td></tr>
                {collect_info}
            </table>
            <table class="invoice-items-table">
                {standard_table_th}
                {standard_table_td}
            </table>
            <div class="total-words-area">💰 إجمالي المبلغ باللغة العربية: <span style="color:#000;">{arabic_total_words}</span></div>
            <div class="invoice-footer-alert">⚠️ تنبيه: مدة الاستبدال والارتجاع 15 يوماً من تاريخ الفاتورة بشرط سلامة الغلاف الأصلي.</div>
        </div>

        <div class="invoice-page">
            <div class="invoice-header">
                <h3>📋 نسخة الإدارة المالية والحسابات</h3>
                <h1>🏢 {sh_name}</h1>
                <p>العنوان: {sh_address}</p>
            </div>
            <table class="invoice-details-table">
                <tr><td><b>رقم الفاتورة:</b> {inv_id}</td><td><b>التاريخ والوقت:</b> {datetime_str}</td></tr>
                <tr><td><b>اسم العميل:</b> {client_name}</td><td><b>الهاتف:</b> {phone if phone else 'غير محدد'}</td></tr>
                <tr><td><b>نوع الدفع:</b> {pay_type}</td><td><b>المسؤول:</b> {user}</td></tr>
                <tr><td><b>الإجمالي الكلي:</b> {total_invoice_amount} جنيه</td><td></td></tr>
                {collect_info}
            </table>
            <table class="invoice-items-table">
                {standard_table_th}
                {standard_table_td}
            </table>
            <div class="total-words-area">💰 إجمالي المبلغ باللغة العربية: <span style="color:#000;">{arabic_total_words}</span></div>
        </div>

        <div class="invoice-page">
            <div class="invoice-header">
                <h3>📦 نسخة مسؤول المخازن والصرف</h3>
                <h1>🏢 {sh_name}</h1>
                <p>التوجيه: يرجى صرف الأصناف المبينة أدناه لمستلم الفاتورة</p>
            </div>
            <table class="invoice-details-table">
                <tr><td><b>رقم الفاتورة:</b> {inv_id}</td><td><b>التاريخ والوقت:</b> {datetime_str}</td></tr>
                <tr><td><b>اسم العميل:</b> {client_name}</td><td><b>المسؤول المصدر:</b> {user}</td></tr>
                <tr><td><b>نوع الدفع:</b> {pay_type}</td><td><b>حالة الإذن:</b> جاهز للصرف</td></tr>
            </table>
            <table class="invoice-items-table">
                {store_table_th}
                {store_table_td}
            </table>
            <div class="invoice-footer-alert" style="margin-top:40px;">توقيع أمين المخزن: ............................ | توقيع المستلم: ............................</div>
        </div>
    </div>
    """
    return html_content

def get_download_link(html_content, filename="invoice.html"):
    b64 = base64.b64encode(html_content.encode('utf-8-sig')).decode()
    return f'<div class="download-btn-area"><a href="data:text/html;base64,{b64}" download="{filename}" style="display: block; padding: 12px; color: white; background-color: #007bff; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center; margin: 15px auto; max-width:400px;">📥 اضغط هنا لتنزيل وحفظ ملف الفاتورة في التحميلات فوراً</a></div>'

if not st.session_state.auth:
    st.title(f"🏢 نظام {SHOWROOM_NAME} - تسجيل الدخول")
    user_input = st.text_input("اسم المستخدم", key="login_user").strip()
    pw_input = st.text_input("كلمة المرور", type="password", key="login_pw").strip()
    
    if st.button("دخول للنظام", use_container_width=True):
        u_df = pd.read_csv(USERS_FILE, dtype=str)
        match = u_df[(u_df['username'] == user_input) & (u_df['password'] == pw_input)]
        if not match.empty:
            st.session_state.auth = True
            st.session_state.user = user_input
            st.session_state.role = match.iloc[0]['role']
            st.success(f"مرحباً بك يا {user_input} ({st.session_state.role})")
            st.rerun()
        else: st.error("بيانات الدخول خاطئة.")
else:
    perms_df = pd.read_csv(PERMISSIONS_FILE)
    current_role = st.session_state.role
    
    allowed_actions = perms_df[perms_df[current_role] == True]["اسم الصفحة"].tolist()
    sidebar_pages = [p for p in allowed_actions]
    
    if not sidebar_pages: sidebar_pages = ["🔍 حالة المخزن"]
        
    st.sidebar.title(f"👤 {st.session_state.user}")
    st.sidebar.write(f"الرتبة: **{st.session_state.role}**")
    
    choice = st.sidebar.selectbox("الانتقال إلى الأقسام الرئيسية", sidebar_pages)
    
    # استدعاء البيانات من الـ Session State
    inv_df = st.session_state.inv_df
    sales_df = st.session_state.sales_df
    returns_df = st.session_state.returns_df
    purchases_df = st.session_state.purchases_df
    exp_df = st.session_state.exp_df
    att_df = st.session_state.att_df
    contacts_df = st.session_state.contacts_df

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth = False
        st.session_state.cart = []
        st.rerun()

    def safe_item_format(x):
        if inv_df.empty: return str(x)
        match = inv_df[inv_df['كود الصنف'] == x]['اسم الصنف'].values
        return f"{x} - {match[0]}" if len(match) > 0 else f"{x} - (صنف غير معروف)"

    # --- 1. صفحة إدارة الأصناف ---
    if "إدارة الأصناف والمخزن" in choice:
        st.header("📦 إدارة وتكويد أصناف المخزن المتطورة")
        t_view, t_add, t_edit, t_delete = st.tabs(["📋 استعراض المنتجات", "➕ تكويد صنف جديد", "✏️ تعديل أسعار صنف", "❌ حذف صنف من النظام"])
        
        with t_view:
            st.dataframe(inv_df, use_container_width=True)
            
        with t_add:
            st.subheader("إضافة منتج جديد بالتفاصيل الجديدة")
            c1, c2, c3, c4 = st.columns(4)
            iid = c1.text_input("كود الصنف (الباركود)").strip()
            iname = c2.text_input("اسم المنتج").strip()
            icat = c3.selectbox("تصنيف الصنف", ["كهربي", "منزلي", "بلاستيك", "صيني ومطابخ", "منظفات", "عام أخري"])
            iunit = c4.selectbox("نوع الوحدة", ["قطعة", "طقم", "كرتونة", "دسته", "كيلو"])
            
            c5, c6, c7 = st.columns(3)
            iwh = c5.text_input("موقع المخزن / الرف", value="المخزن الرئيسي").strip()
            ipurchase = c6.number_input("سعر الشراء الافتراضي", min_value=0.0, step=1.0)
            isale = c7.number_input("سعر البيع الافتراضي", min_value=0.0, step=1.0)
            
            if st.button("تكويد وحفظ البند"):
                if iid and iname:
                    if iid in inv_df["كود الصنف"].values: st.warning("⚠️ هذا الكود مسجل مسبقاً!")
                    else:
                        new_item = pd.DataFrame([{"كود الصنف": iid, "اسم الصنف": iname, "تصنيف الصنف": icat, "نوع الوحدة": iunit, "موقع المخزن": iwh, "الكمية": 0, "سعر الشراء": ipurchase, "سعر البيع": isale}])
                        st.session_state.inv_df = pd.concat([inv_df, new_item], ignore_index=True)
                        st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                        st.success("🎉 تم تكويد المنتج بنجاح وحفظه!")
                        st.rerun()

        with t_edit:
            st.subheader("تعديل تفاصيل وأسعار صنف حالي")
            if inv_df.empty: 
                st.info("لا توجد أصناف مسجلة لتعديلها.")
            else:
                selected_edit_code = st.selectbox("اختر الصنف المراد تعديله", inv_df["كود الصنف"].values, format_func=safe_item_format)
                matching_rows = inv_df[inv_df["كود الصنف"] == selected_edit_code]
                if matching_rows.empty:
                    st.warning("⚠️ الصنف المحدد غير متوفر أو تم حذفه.")
                else:
                    row_idx = matching_rows.index[0]
                    
                    ec1, ec2, ec3 = st.columns(3)
                    updated_cat = ec1.selectbox("تعديل التصنيف", ["كهربي", "منزلي", "بلاستيك", "صيني ومطابخ", "منظفات", "عام أخري"], index=["كهربي", "منزلي", "بلاستيك", "صيني ومطابخ", "منظفات", "عام أخري"].index(inv_df.at[row_idx, "تصنيف الصنف"]) if inv_df.at[row_idx, "تصنيف الصنف"] in ["كهربي", "منزلي", "بلاستيك", "صيني ومطابخ", "منظفات", "عام أخري"] else 0)
                    updated_unit = ec2.selectbox("تعديل الوحدة", ["قطعة", "طقم", "كرتونة", "دسته", "كيلو"], index=["قطعة", "طقم", "كرتونة", "دسته", "كيلو"].index(inv_df.at[row_idx, "نوع الوحدة"]) if inv_df.at[row_idx, "نوع الوحدة"] in ["قطعة", "طقم", "كرتونة", "دسته", "كيلو"] else 0)
                    updated_wh = ec3.text_input("تعديل موقع المخزن", value=str(inv_df.at[row_idx, "موقع المخزن"]))
                    
                    ec4, ec5 = st.columns(2)
                    updated_purchase = ec4.number_input("سعر الشراء الجديد", value=float(inv_df.at[row_idx, "سعر الشراء"]), min_value=0.0)
                    updated_sale = ec5.number_input("سعر البيع الجديد", value=float(inv_df.at[row_idx, "سعر البيع"]), min_value=0.0)
                    
                    if st.button("💾 حفظ الأسعار والتفاصيل الجديدة"):
                        st.session_state.inv_df.at[row_idx, "تصنيف الصنف"] = updated_cat
                        st.session_state.inv_df.at[row_idx, "نوع الوحدة"] = updated_unit
                        st.session_state.inv_df.at[row_idx, "موقع المخزن"] = updated_wh
                        st.session_state.inv_df.at[row_idx, "سعر الشراء"] = updated_purchase
                        st.session_state.inv_df.at[row_idx, "سعر البيع"] = updated_sale
                        
                        st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                        st.success("✅ تم تحديث بيانات البند بنجاح!")
                        st.rerun()

        with t_delete:
            st.subheader("❌ حذف صنف نهائياً")
            if inv_df.empty: 
                st.info("لا توجد أصناف بالمخزن.")
            else:
                selected_del_code = st.selectbox("اختر الصنف المراد حذفه تماماً", inv_df["كود الصنف"].values, format_func=safe_item_format, key="del_box")
                st.warning("⚠️ انتبه! حذف الصنف سيؤدي لإزالته كلياً من جرد المخزن الحركي.")
                if st.button("🔥 تأكيد الحذف النهائي للصنف"):
                    st.session_state.inv_df = inv_df[inv_df["كود الصنف"] != selected_del_code]
                    st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                    st.success("🗑️ تم حذف المنتج من النظام بنجاح!")
                    st.rerun()

    # --- 2. صفحة رفع رصيد أول المدة ---
    elif "رصيد أول المدة" in choice:
        st.header("📊 رفع وتثبيت رصيد أول المدة ومخزون البضائع")
        
        t_paste, t_file = st.tabs(["📋 خاصية اللصق السريع المباشر", "📥 رفع ملف Excel"])
        
        def process_and_merge_data(imported_df):
            try:
                imported_df.columns = imported_df.columns.str.strip()
                if "كود الصنف" in imported_df.columns:
                    imported_df["كود الصنف"] = imported_df["كود الصنف"].astype(str)
                    
                    combined = pd.concat([st.session_state.inv_df, imported_df]).drop_duplicates(subset=['كود الصنف'], keep='last')
                    st.session_state.inv_df = combined
                    st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                    st.success("🚀 تم دمج وحفظ البيانات في رصيد أول المدة بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ فشل الدمج: تأكد من احتواء العناوين الملصوقة أو المرفوعة على حقل 'كود الصنف'.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء ترحيل البيانات: {e}")

        with t_paste:
            st.markdown("💡 **انسخ البيانات من جداول الـ Excel بالكامل (بما فيها صف العناوين الرئيسي) ثم الصقها بالأسفل:**")
            pasted_input = st.text_area("قم باللصق هنا (Ctrl + V)", height=250, placeholder="كود الصنف\tاسم الصنف\tتصنيف الصنف...")
            
            if pasted_input.strip():
                try:
                    paste_df = pd.read_csv(StringIO(pasted_input), sep="\t")
                    st.write("🔍 **معاينة حية للبيانات التي قمت بلصقها:**")
                    st.dataframe(paste_df, use_container_width=True)
                    
                    if st.button("🚀 ترحيل وحفظ البيانات الملصوقة فوراً بالقاعدة"):
                        process_and_merge_data(paste_df)
                except Exception as ex:
                    st.error(f"🚨 عذراً، لم نتمكن من تحليل النص الملصوق. تأكد من نسخ جدول Excel كامل بالعناوين بشكل صحيح: {ex}")

        with t_file:
            st.info("💡 تأكد أن ملف الـ Excel يحتوي على الأعمدة التالية ليعمل بشكل سليم: (كود الصنف، اسم الصنف، تصنيف الصنف، نوع الوحدة، موقع المخزن، الكمية، سعر الشراء، سعر البيع)")
            uploaded_file = st.file_uploader("اختر شيت الاكسل الخاص بالبضائع", type=["xlsx", "xls"])
            if uploaded_file is not None:
                try:
                    excel_df = pd.read_excel(uploaded_file, dtype={"كود الصنف": str})
                    st.dataframe(excel_df)
                    if st.button("تأكيد ودمج الملف في رصيد أول المدة"):
                        process_and_merge_data(excel_df)
                except Exception as e: st.error(f"❌ حدث خطأ أثناء قراءة الملف: {e}")

    # --- 3. صفحة حالة المخزن ---
    elif "حالة المخزن" in choice:
        st.header("🔍 جرد بضائع المخزن الحالية ومواقع تواجدها")
        st.dataframe(inv_df, use_container_width=True)

    # --- 4. صفحة العملاء والموردين ---
    elif "العملاء والموردين" in choice:
        st.header("🤝 إدارة بيانات العملاء والموردين")
        st.dataframe(contacts_df, use_container_width=True)
        c1, c2, c3, c4 = st.columns(4)
        ctype = c1.selectbox("النوع", ["عميل", "مورد"])
        cname = c2.text_input("الاسم")
        cphone = c3.text_input("الهاتف")
        caddress = c4.text_input("العنوان")
        if st.button("حفظ الجهة"):
            if cname:
                new_c = pd.DataFrame([{"النوع": ctype, "الاسم": cname, "الهاتف": cphone, "العنوان": caddress}])
                st.session_state.contacts_df = pd.concat([contacts_df, new_c], ignore_index=True)
                st.session_state.contacts_df.to_csv(CONTACTS_FILE, index=False, encoding='utf-8-sig')
                st.success("✅ تم الحفظ بنجاح!")
                st.rerun()

    # --- 5. صفحة حركة فواتير الشراء ---
    elif "حركة فواتير الشراء" in choice:
        st.header("📥 تسجيل وإدارة فواتير المشتريات والوارد")
        t_new, t_manage = st.tabs(["📥 تسجيل فاتورة شراء جديدة", "✏️ مراجعة وحذف الفواتير القديمة"])
        
        with t_new:
            if inv_df.empty: st.warning("⚠️ قم بتكويد بضائع أولاً.")
            else:
                m_list = contacts_df[contacts_df['النوع'] == 'مورد']['الاسم'].unique()
                if len(m_list) == 0: m_list = ["مورد عام"]
                c1, c2, c3, c4 = st.columns(4)
                vendor = c1.selectbox("المورد", m_list)
                
                selected_item_code = c2.selectbox("الصنف المشترى", inv_df['كود الصنف'].values, format_func=safe_item_format)
                matching_items = inv_df[inv_df['كود الصنف'] == selected_item_code]
                if matching_items.empty:
                    st.warning("الصنف المحدد غير متوفر.")
                else:
                    item_row = matching_items.iloc[0]
                    default_pur_price = float(item_row['سعر الشراء']) if 'سعر الشراء' in item_row else 0.0
                    actual_purchase_price = c3.number_input("سعر الشراء المعتمد لهذه الفاتورة", value=default_pur_price, min_value=0.0)
                    qty = c4.number_input("الكمية المشتراة", min_value=1, step=1)
                    
                    total = actual_purchase_price * qty
                    if st.button("حفظ المشتريات وإدخلها للمخزن المحدد"):
                        idx = inv_df[inv_df['كود الصنف'] == selected_item_code].index[0]
                        st.session_state.inv_df.at[idx, 'الكمية'] = int(inv_df.at[idx, 'الكمية']) + qty
                        st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                        
                        pur_id = "PUR-" + str(int(datetime.now().timestamp()))
                        new_p = pd.DataFrame([{"رقم الفاتورة": pur_id, "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "المورد": vendor, "كود الصنف": selected_item_code, "الصنف": item_row['اسم الصنف'], "تصنيف الصنف": item_row['تصنيف الصنف'], "نوع الوحدة": item_row['نوع الوحدة'], "موقع المخزن": item_row['موقع المخزن'], "سعر الشراء المعتمد": str(actual_purchase_price), "الكمية": str(qty), "إجمالي الشراء": str(total), "المسؤول": st.session_state.user}])
                        st.session_state.purchases_df = pd.concat([purchases_df, new_p], ignore_index=True)
                        st.session_state.purchases_df.to_csv(PURCHASES_FILE, index=False, encoding='utf-8-sig')
                        st.success("✅ تم تسجيل الوارد وتحديث المخزن والـ Session بنجاح!")
                        st.rerun()
                        
        with t_manage:
            st.subheader("⚙️ مراجعة وحذف فواتير الشراء السابقة")
            if purchases_df.empty: st.info("لا توجد فواتير شراء مسجلة حالياً.")
            else:
                st.dataframe(purchases_df, use_container_width=True)
                target_pur_id = st.selectbox("اختر رقم فاتورة الشراء للإجراء", purchases_df["رقم الفاتورة"].unique())
                p_row = purchases_df[purchases_df["رقم الفاتورة"] == target_pur_id].iloc[0]
                
                if st.button("❌ حذف فاتورة الشراء هذه بالكامل وخصمها من المخزن", use_container_width=True):
                    p_code = p_row["كود الصنف"]
                    p_qty = int(p_row["الكمية"])
                    if p_code in inv_df["كود الصنف"].values:
                        inv_idx = inv_df[inv_df["كود الصنف"] == p_code].index[0]
                        st.session_state.inv_df.at[inv_idx, "الكمية"] = max(0, int(inv_df.at[inv_idx, "الكمية"]) - p_qty)
                        st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                    
                    st.session_state.purchases_df = purchases_df[purchases_df["رقم الفاتورة"] != target_pur_id]
                    st.session_state.purchases_df.to_csv(PURCHASES_FILE, index=False, encoding='utf-8-sig')
                    st.success("🔥 تم حذف فاتورة الشراء وتعديل رصيد المخزن!")
                    st.rerun()

    # --- 6. صفحة حركة فواتير البيع ---
    elif "حركة فواتير البيع" in choice:
        st.header(f"📤 إنشاء فاتورة مبيعات جديدة - {SHOWROOM_NAME}")
        if inv_df.empty: 
            st.warning("⚠️ لا يمكن إتمام عملية البيع لأن المخزن فارغ تماماً.")
        else:
            c_list = contacts_df[contacts_df['النوع'] == 'عميل']['الاسم'].unique()
            c1, c2, c3, c4 = st.columns(4)
            cust_type = c1.radio("نوع العميل", ["سريع / غير مسجل", "مسجل مسبقاً"])
            
            c_phone = ""
            c_address = ""
            if cust_type == "مسجل مسبقاً" and len(c_list) > 0:
                c_name = c2.selectbox("اختر العميل", c_list)
                c_address = contacts_df[contacts_df['الاسم'] == c_name]['العنوان'].values[0] if len(contacts_df[contacts_df['الاسم'] == c_name]) > 0 else ""
                c_phone = contacts_df[contacts_df['الاسم'] == c_name]['الهاتف'].values[0] if len(contacts_df[contacts_df['الاسم'] == c_name]) > 0 else ""
            else:
                c_name = c2.text_input("اسم العميل")
                c_phone = c3.text_input("رقم هاتف العميل")
                c_address = c4.text_input("عنوان العميل")
            
            visit_count = 0
            if c_name and not sales_df.empty:
                visit_count = len(sales_df[sales_df["اسم العميل"] == c_name]['رقم الفاتورة'].unique())
                
            st.info(f"📊 عدد زيارات ومبيعات هذا العميل السابقة: **{visit_count}** مرة")
            
            st.markdown("---")
            cc1, cc2, cc3 = st.columns(3)
            sale_type = cc1.selectbox("طبيعة البيع", ["نقدي (كاش)", "آجل (على الحساب)"])
            
            collect_system = "دفعة كاملة كاش"
            collect_date = "فورياً"
            if sale_type == "آجل (على الحساب)":
                collect_system = cc2.selectbox("نظام تحصيل الفاتورة الآجلة", ["دفعة واحدة لاحقاً", "أقساط أسبوعية", "أقساط شهرية", "نظام دفعات مخصصة"])
                collect_date = str(cc3.date_input("تاريخ التحصيل المستهدف"))
            
            st.markdown("### 🛒 إضافة المنتجات إلى السلة")
            c5, c6, c7, c8 = st.columns(4)
            selected_item_code = c5.selectbox("اختر المنتج بالكود", inv_df['كود الصنف'].values, format_func=safe_item_format)
            
            matching_items = inv_df[inv_df['كود الصنف'] == selected_item_code]
            if not matching_items.empty:
                item_row = matching_items.iloc[0]
                default_price = float(item_row['سعر البيع'])
                
                if st.session_state.role in ["مدير", "مشرف"]:
                    unit_price = c6.number_input("سعر بيع القطعة الحالية (يمكنك تعديله)", value=default_price, min_value=0.0)
                else:
                    c6.write(f"🔒 السعر الافتراضي: **{default_price} جنيه**")
                    unit_price = default_price
                    
                qty = c7.number_input("الكمية المطلوبة", min_value=1, step=1)
                
                discount = 0.0
                if st.session_state.role in ["مدير", "مشرف"]:
                    discount = c8.number_input("نسبة الخصم الممنوحة (%)", min_value=0.0, max_value=100.0, step=0.5)
                else: c8.write("🔒 *الخصومات مغلقة للموظفين*")
                
                subtotal = unit_price * qty
                discount_amount = subtotal * (discount / 100)
                final_total = subtotal - discount_amount
                
                cost_basis = float(item_row['سعر الشراء']) * qty
                profit_basis = final_total - cost_basis
                
                st.warning(f"📊 المتوفر بالمخزن: {item_row['الكمية']} {item_row['نوع الوحدة']} | موقع التواجد: {item_row['موقع المخزن']}")
                
                if st.button("➕ إضافة المنتج الحالي للسلة"):
                    already_in_cart = sum(item['qty'] for item in st.session_state.cart if item['item_code'] == selected_item_code)
                    if int(item_row['الكمية']) < (qty + already_in_cart):
                        st.error("❌ الكمية المطلوبة غير متوفرة بالمخزن الحركي!")
                    else:
                        st.session_state.cart.append({
                            "item_code": selected_item_code,
                            "item_name": item_row['اسم الصنف'],
                            "category": item_row['تصنيف الصنف'],
                            "unit": item_row['نوع الوحدة'],
                            "warehouse_loc": item_row['موقع المخزن'],
                            "qty": qty,
                            "price": unit_price,
                            "discount": discount,
                            "final_total": final_total,
                            "cost_basis": cost_basis,
                            "profit_basis": profit_basis
                        })
                        st.success(f"🎉 تم إضافة {item_row['اسم الصنف']} إلى السلة!")
                        st.rerun()
            
            if st.session_state.cart:
                st.markdown("---")
                st.markdown("### 📋 محتويات السلة الحالية:")
                
                updated_cart = []
                need_rerun = False
                
                for i, item in enumerate(st.session_state.cart):
                    with st.container():
                        st.markdown(f"**📦 {i+1}. {item['item_name']}** ({item['unit']})")
                        col_edit1, col_edit2, col_edit3, col_del = st.columns([2, 2, 2, 1])
                        
                        new_qty = col_edit1.number_input(f"الكمية", min_value=1, value=int(item['qty']), key=f"cart_qty_{i}_{item['item_code']}")
                        
                        if st.session_state.role in ["مدير", "مشرف"]:
                            new_price = col_edit2.number_input(f"السعر (جنيه)", min_value=0.0, value=float(item['price']), key=f"cart_price_{i}_{item['item_code']}")
                            new_discount = col_edit3.number_input(f"الخصم %", min_value=0.0, max_value=100.0, value=float(item['discount']), key=f"cart_disc_{i}_{item['item_code']}")
                        else:
                            col_edit2.write(f"السعر: {item['price']} ج")
                            col_edit3.write(f"الخصم: {item['discount']}%")
                            new_price = item['price']
                            new_discount = item['discount']
                            
                        is_deleted = col_del.button("❌ حذف", key=f"cart_del_{i}_{item['item_code']}")
                        
                        if not is_deleted:
                            match_inv = inv_df[inv_df['كود الصنف'] == item['item_code']].iloc[0]
                            sub_t = new_price * new_qty
                            disc_a = sub_t * (new_discount / 100)
                            f_total = sub_t - disc_a
                            c_basis = float(match_inv['سعر الشراء']) * new_qty
                            p_basis = f_total - c_basis
                            
                            updated_cart.append({
                                "item_code": item['item_code'],
                                "item_name": item['item_name'],
                                "category": item['category'],
                                "unit": item['unit'],
                                "warehouse_loc": item['warehouse_loc'],
                                "qty": new_qty,
                                "price": new_price,
                                "discount": new_discount,
                                "final_total": f_total,
                                "cost_basis": c_basis,
                                "profit_basis": p_basis
                            })
                            
                            if (new_qty != item['qty']) or (new_price != item['price']) or (new_discount != item['discount']):
                                need_rerun = True
                        else:
                            need_rerun = True
                            
                        st.markdown(f"💰 الصافي للبند: **{item['final_total']:,.2f} جنيه**")
                        st.markdown("---")
                
                if need_rerun:
                    st.session_state.cart = updated_cart
                    st.rerun()

                st.markdown("---")
                col_clear, col_submit = st.columns(2)
                if col_clear.button("🗑️ تفريغ السلة كاملة والبدء من جديد"):
                    st.session_state.cart = []
                    st.rerun()
                    
                if col_submit.button("🧾 إنهاء وحفظ وإصدار الفاتورة الثلاثية (A5)", use_container_width=True):
                    if not c_name: st.error("❌ يرجى تحديد أو كتابة اسم العميل أولاً.")
                    elif not st.session_state.cart: st.error("❌ السلة فارغة!")
                    else:
                        inv_id = "INV-" + str(int(datetime.now().timestamp()))
                        current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        new_sales_entries = []
                        for item in st.session_state.cart:
                            idx = inv_df[inv_df['كود الصنف'] == item['item_code']].index[0]
                            st.session_state.inv_df.at[idx, 'الكمية'] = int(inv_df.at[idx, 'الكمية']) - item['qty']
                            
                            new_sales_entries.append({
                                "رقم الفاتورة": inv_id,
                                "التاريخ": current_datetime_str,
                                "اسم العميل": c_name,
                                "هاتف العميل": c_phone,
                                "العنوان": c_address,
                                "نوع البيع": sale_type,
                                "نظام التحصيل": collect_system,
                                "تاريخ التحصيل": collect_date,
                                "كود الصنف": item['item_code'],
                                "الصنف": item['item_name'],
                                "تصنيف الصنف": item['category'],
                                "نوع الوحدة": item['unit'],
                                "موقع المخزن": item['warehouse_loc'],
                                "الكمية": str(item['qty']),
                                "سعر الوحدة": str(item['price']),
                                "الخصم %": str(item['discount']),
                                "إجمالي البيع": str(item['final_total']),
                                "تكلفة الشراء الإجمالية": str(item['cost_basis']),
                                "صافي ربح الفاتورة": str(item['profit_basis']),
                                "المسؤول": st.session_state.user
                            })
                        
                        st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                        st.session_state.sales_df = pd.concat([sales_df, pd.DataFrame(new_sales_entries)], ignore_index=True)
                        st.session_state.sales_df.to_csv(SALES_FILE, index=False, encoding='utf-8-sig')
                        
                        st.success("🎉 تم تسجيل وحفظ الفاتورة بالكامل بنجاح في النظام!")
                        
                        triple_html = generate_triple_invoice_html(inv_id, current_datetime_str, c_name, c_phone, c_address, sale_type, collect_system, collect_date, st.session_state.user, st.session_state.cart, SHOWROOM_NAME, SHOWROOM_ADDRESS, INQUIRY_NUMBER)
                        st.markdown(get_download_link(triple_html, f"الفاتورة_الثلاثية_{inv_id}.html"), unsafe_allow_html=True)
                        st.markdown(triple_html, unsafe_allow_html=True)
                        
                        st.session_state.cart = []

    # --- 7. صفحة ارتجاع فواتير البيع (البند الجديد والمطلوب) ---
    elif "ارتجاع فواتير البيع" in choice:
        st.header("↩️ منظومة ارتجاع المبيعات ومردودات الفواتير")
        
        if sales_df.empty:
            st.info("لا توجد فواتير مبيعات مسجلة في السجلات ليتم إرجاعها.")
        else:
            invoice_search = st.text_input("🔍 ابحث برقم الفاتورة الأصلية أو اسم العميل لإجراء المرتجع").strip()
            
            if invoice_search:
                matching_sales = sales_df[sales_df['رقم الفاتورة'].str.contains(invoice_search, case=False) | sales_df['اسم العميل'].str.contains(invoice_search, case=False)]
            else:
                matching_sales = sales_df
                
            st.dataframe(matching_sales, use_container_width=True)
            
            if not matching_sales.empty:
                selected_ret_inv = st.selectbox("اختر رقم الفاتورة التي تحتوي على الأصناف المراد إرجاعها", matching_sales['رقم الفاتورة'].unique())
                invoice_items = sales_df[sales_df['رقم الفاتورة'] == selected_ret_inv]
                
                st.markdown("### 📦 البضائع المدرجة في هذه الفاتورة:")
                for idx, row in invoice_items.iterrows():
                    item_code = row['كود الصنف']
                    item_name = row['الصنف']
                    purchased_qty = int(row['الكمية'])
                    item_price = float(row['إجمالي البيع']) / purchased_qty if purchased_qty > 0 else 0
                    
                    # التحقق من الكميات التي تم إرجاعها مسبقاً لهذا الصنف في هذه الفاتورة
                    already_returned = 0
                    if not returns_df.empty:
                        already_returned = returns_df[(returns_df['رقم الفاتورة الأصلية'] == selected_ret_inv) & (returns_df['كود الصنف'] == item_code)]['الكمية المرجعة'].astype(int).sum()
                    
                    max_allowable_return = purchased_qty - already_returned
                    
                    st.write(f"🔹 **{item_name}** | الكود: `{item_code}` | الكمية المشترات أصلاً: **{purchased_qty}** | تم إرجاع مسبقاً: **{already_returned}**")
                    
                    if max_allowable_return <= 0:
                        st.success("🔒 تم إرجاع كامل كمية هذا البند بنجاح.")
                    else:
                        ret_qty = st.number_input(f"الكمية المراد إرجاعها من {item_name}", min_value=0, max_value=max_allowable_return, value=0, key=f"ret_qty_{idx}")
                        
                        if ret_qty > 0:
                            refund_amount = ret_qty * (float(row['سعر الوحدة']) * (1 - float(row['الخصم %'])/100))
                            st.markdown(f"💰 المبلغ المالي الذي سيرد للعميل: **{refund_amount:,.2f} جنيه**")
                            
                            if st.button(f"↩️ تأكيد إرجاع {ret_qty} من {item_name}", key=f"btn_ret_{idx}"):
                                # 1. إعادة المنتج للمخزن وتحديث رصيد المخزن
                                if item_code in inv_df['كود الصنف'].values:
                                    inv_idx = inv_df[inv_df['كود الصنف'] == item_code].index[0]
                                    st.session_state.inv_df.at[inv_idx, 'الكمية'] = int(inv_df.at[inv_idx, 'الكمية']) + ret_qty
                                    st.session_state.inv_df.to_csv(INVENTORY_FILE, index=False, encoding='utf-8-sig')
                                
                                # 2. تعديل كمية المبيعات وأرباح الفاتورة في ملف المبيعات لتعديل التقارير
                                sales_row_idx = sales_df[sales_df['رقم الفاتورة'] == selected_ret_inv].index[0]
                                current_sales_qty = int(sales_df.at[sales_row_idx, 'الكمية'])
                                
                                # حفظ المرتجع بملف منفصل للمراقبة
                                return_id = "RET-" + str(int(datetime.now().timestamp()))
                                new_return_row = pd.DataFrame([{
                                    "رقم الإرجاع": return_id,
                                    "رقم الفاتورة الأصلية": selected_ret_inv,
                                    "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "اسم العميل": row['اسم العميل'],
                                    "كود الصنف": item_code,
                                    "الصنف": item_name,
                                    "الكمية المرجعة": str(ret_qty),
                                    "المبلغ المردود": str(refund_amount),
                                    "المسؤول": st.session_state.user
                                }])
                                st.session_state.returns_df = pd.concat([returns_df, new_return_row], ignore_index=True)
                                st.session_state.returns_df.to_csv(RETURNS_FILE, index=False, encoding='utf-8-sig')
                                
                                st.success(f"✅ تم معالجة المرتجع، وإدخال البضاعة للمخزن، وسيتم ترحيل التسويات الحسابية فوراً!")
                                st.rerun()

            st.markdown("---")
            st.subheader("📋 سجل فواتير الإرجاع والمرتودات السابقة")
            st.dataframe(returns_df, use_container_width=True)

    # --- 8. صفحة البحث عن الفواتير وطباعتها ---
    elif "البحث عن الفواتير وطباعتها" in choice:
        st.header("🔎 نظام البحث والمراجعة وطباعة الفواتير")
        if sales_df.empty: st.info("لا توجد فواتير مبيعات مسجلة في النظام حتى الآن.")
        else:
            search_query = st.text_input("ابحث عن فاتورة مبيعات (أدخل رقم الفاتورة، اسم العميل أو الهاتف)").strip()
            if search_query:
                filtered_sales = sales_df[sales_df['رقم الفاتورة'].str.contains(search_query, case=False, na=False) | sales_df['اسم العميل'].str.contains(search_query, case=False, na=False)]
            else: filtered_sales = sales_df
                
            st.dataframe(filtered_sales, use_container_width=True)
            
            if not filtered_sales.empty:
                selected_inv_id = st.selectbox("اختر رقم الفاتورة لإعادة الطباعة والسحب", filtered_sales['رقم الفاتورة'].unique())
                invoice_rows = sales_df[sales_df['رقم الفاتورة'] == selected_inv_id]
                f_row = invoice_rows.iloc[0]
                
                rebuild_cart = []
                for _, r in invoice_rows.iterrows():
                    rebuild_cart.append({
                        "item_name": r['الصنف'],
                        "category": r.get('تصنيف الصنف', 'عام'),
                        "unit": r.get('نوع الوحدة', 'قطعة'),
                        "warehouse_loc": r.get('موقع المخزن', 'الرئيسي'),
                        "qty": int(r['الكمية']),
                        "price": float(r['سعر الوحدة']) if 'سعر الوحدة' in r else float(r['إجمالي البيع'])/int(r['الكمية']),
                        "discount": float(r['الخصم %']),
                        "final_total": float(r['إجمالي البيع'])
                    })
                
                p_phone = f_row['هاتف العميل'] if 'هاتف العميل' in f_row else ""
                p_sys = f_row['نظام التحصيل'] if 'نظام التحصيل' in f_row else "كاش"
                p_date = f_row['تاريخ التحصيل'] if 'تاريخ التحصيل' in f_row else "فوراً"
                p_time = f_row['التاريخ'] if 'التاريخ' in f_row else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                triple_html = generate_triple_invoice_html(selected_inv_id, p_time, f_row['اسم العميل'], p_phone, f_row['العنوان'], f_row['نوع البيع'], p_sys, p_date, f_row['المسؤول'], rebuild_cart, SHOWROOM_NAME, SHOWROOM_ADDRESS, INQUIRY_NUMBER)
                st.markdown(get_download_link(triple_html, f"إعادة_طباعة_فاتورة_{selected_inv_id}.html"), unsafe_allow_html=True)
                st.markdown(triple_html, unsafe_allow_html=True)

    # --- 9. صفحة تقارير البيع والشراء والأرباح ---
    elif "تقارير البيع والشراء والأرباح" in choice:
        st.header(f"📈 التقارير المالية التفصيلية وحساب الأرباح لـ {SHOWROOM_NAME}")
        
        total_sales = pd.to_numeric(sales_df['إجمالي البيع'], errors='coerce').sum()
        total_purchases = pd.to_numeric(purchases_df['إجمالي الشراء'], errors='coerce').sum()
        total_expenses = pd.to_numeric(exp_df['المبلغ'], errors='coerce').sum()
        total_returned_value = pd.to_numeric(returns_df['المبلغ المردود'], errors='coerce').sum() if not returns_df.empty else 0.0
        
        total_sales_cost = pd.to_numeric(sales_df['تكلفة الشراء الإجمالية'], errors='coerce').sum() if 'تكلفة الشراء الإجمالية' in sales_df else 0.0
        net_profit_actual = (total_sales - total_returned_value) - total_sales_cost - total_expenses
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 صافي المبيعات (بعد المرتجع)", f"{(total_sales - total_returned_value):,.2f} جنيه")
        m2.metric("↩️ إجمالي قيم المردودات", f"{total_returned_value:,.2f} جنيه")
        m3.metric("💸 إجمالي المصاريف العمومية", f"{total_expenses:,.2f} جنيه")
        m4.metric("📊 الصافي الحقيقي للأرباح الدقيقة", f"{net_profit_actual:,.2f} جنيه")
        
        st.markdown("---")
        t_sales_rep, t_purchases_rep = st.tabs(["📋 تقرير حركة المبيعات الشامل", "📋 تقرير حركة المشتريات الشامل"])
        
        with t_sales_rep:
            st.subheader("سجل المبيعات الصادرة")
            st.dataframe(sales_df, use_container_width=True)
            if not sales_df.empty:
                out_sales = BytesIO()
                with pd.ExcelWriter(out_sales, engine='xlsxwriter') as wr:
                    sales_df.to_excel(wr, index=False, sheet_name='المبيعات')
                st.download_button("📥 تحميل تقرير المبيعات بصيغة Excel", data=out_sales.getvalue(), file_name="تقرير_المبيعات_الشامل.xlsx", mime="application/vnd.ms-excel")
                
        with t_purchases_rep:
            st.subheader("سجل حركة المشتريات الواردة")
            st.dataframe(purchases_df, use_container_width=True)
            if not purchases_df.empty:
                out_pur = BytesIO()
                with pd.ExcelWriter(out_pur, engine='xlsxwriter') as wr:
                    purchases_df.to_excel(wr, index=False, sheet_name='المشتريات')
                st.download_button("📥 تحميل تقرير المشتريات بصيغة Excel", data=out_pur.getvalue(), file_name="تقرير_المشتريات_الشامل.xlsx", mime="application/vnd.ms-excel")

    # --- 10. صفحة المصاريف ---
    elif "المصاريف" in choice:
        st.header("💸 تسجيل المصاريف الإدارية والعمومية")
        st.dataframe(exp_df, use_container_width=True)
        b1 = st.text_input("بيان الصرف")
        b2 = st.number_input("المبلغ المنصرف", min_value=0.0, step=10.0)
        if st.button("حفظ المصروف"):
            if b1 and b2 > 0:
                new_e = pd.DataFrame([{"التاريخ": datetime.now().strftime("%Y-%m-%d"), "البيان": b1, "المبلغ": b2, "المسؤول": st.session_state.user}])
                st.session_state.exp_df = pd.concat([exp_df, new_e], ignore_index=True)
                st.session_state.exp_df.to_csv(EXPENSES_FILE, index=False, encoding='utf-8-sig')
                st.success("✅ تم حفظ البند مصروفات!")
                st.rerun()

    # --- 11. الحضور والانصراف ---
    elif "الحضور والانصراف" in choice:
        st.header("⏰ نظام تسجيل الحضور والانصراف")
        st.subheader(f"المستخدم الحالي: ({st.session_state.user})")
        col_att1, col_att2 = st.columns(2)
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if col_att1.button("🟢 تسجيل حركة حضور الآن", use_container_width=True):
            match = att_df[(att_df["الموظف"] == st.session_state.user) & (att_df["التاريخ"] == current_date)]
            if not match.empty: st.warning("⚠️ أنت مسجل حضور بالفعل لهذا اليوم!")
            else:
                new_attendance = pd.DataFrame([{"الموظف": st.session_state.user, "التاريخ": current_date, "وقت الحضور": current_time, "وقت الانصراف": "لم ينصرف بعد"}])
                st.session_state.att_df = pd.concat([att_df, new_attendance], ignore_index=True)
                st.session_state.att_df.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')
                st.success(f"🎉 تم تسجيل الحضور بنجاح عند الساعة: {current_time}")
                st.rerun()
                
        if col_att2.button("🔴 تسجيل حركة انصراف الآن", use_container_width=True):
            idx_match = att_df[(att_df["الموظف"] == st.session_state.user) & (att_df["التاريخ"] == current_date)].index
            if len(idx_match) > 0:
                st.session_state.att_df.at[idx_match[0], "وقت الانصراف"] = current_time
                st.session_state.att_df.to_csv(ATTENDANCE_FILE, index=False, encoding='utf-8-sig')
                st.success(f"🚀 تم تسجيل الانصراف بنجاح عند الساعة: {current_time}")
                st.rerun()
            else: st.error("❌ لم يتم العثور على حركة حضور مسجلة لك اليوم لتسجيل الانصراف عليها!")

        st.markdown("---")
        st.dataframe(att_df, use_container_width=True)

    # --- 12. صفحة إدارة وتعديل الحسابات ---
    elif "إدارة وتعديل الصلاحيات والحسابات" in choice:
        st.header("⚙️ لوحة التحكم في الحسابات وصلاحيات الوصول")
        tab_users, tab_roles = st.tabs(["👤 إدارة وتعديل وحذف الحسابات (اليوزرات)", "🔒 تفعيل وإخفاء صلاحيات الصفحات"])
        
        with tab_users:
            u_df = pd.read_csv(USERS_FILE, dtype=str)
            st.subheader("المستخدمون المقيدون بالنظام حالياً")
            st.dataframe(u_df, use_container_width=True)
            
            st.markdown("---")
            uc1, uc2 = st.columns(2)
            
            with uc1:
                st.subheader("➕ إضافة حساب مستخدم جديد")
                new_username = st.text_input("اسم المستخدم الجديد").strip()
                new_password = st.text_input("كلمة مرور الحساب الجديدة").strip()
                new_role = st.selectbox("الصلاحية الممنوحة", ["مدير", "مشرف", "موظف"])
                if st.button("➕ حفظ وإنشاء المستخدم"):
                    if new_username and new_password:
                        if new_username in u_df["username"].values: st.error("❌ اسم المستخدم مسجل مسبقاً!")
                        else:
                            new_acc = pd.DataFrame([{"username": new_username, "password": new_password, "role": new_role}])
                            u_df = pd.concat([u_df, new_acc], ignore_index=True)
                            u_df.to_csv(USERS_FILE, index=False, encoding='utf-8-sig')
                            st.success(f"🎉 تم إنشاء الحساب بنجاح!")
                            st.rerun()

            with uc2:
                st.subheader("🛠️ تعديل أو حذف مستخدم حالي")
                if len(u_df) > 0:
                    target_user = st.selectbox("اختر الحساب المراد تعديله أو حذفه", u_df["username"].values)
                    target_idx = u_df[u_df["username"] == target_user].index[0]
                    
                    edit_pw = st.text_input("تعديل كلمة المرور", value=u_df.at[target_idx, "password"])
                    edit_role = st.selectbox("تعديل الرتبة", ["مدير", "مشرف", "موظف"], index=["مدير", "مشرف", "موظف"].index(u_df.at[target_idx, "role"]))
                    
                    col_b1, col_b2 = st.columns(2)
                    if col_b1.button("💾 حفظ التعديلات للحساب"):
                        u_df.at[target_idx, "password"] = edit_pw
                        u_df.at[target_idx, "role"] = edit_role
                        u_df.to_csv(USERS_FILE, index=False, encoding='utf-8-sig')
                        st.success("✅ تم تحديث بيانات المستخدم!")
                        st.rerun()
                        
                    if col_b2.button("🗑️ حذف هذا الحساب نهائياً"):
                        if target_user == "admin": st.error("❌ لا يمكن حذف الحساب الإداري الرئيسي (admin) لمنع قفل النظام!")
                        else:
                            u_df = u_df[u_df["username"] != target_user]
                            u_df.to_csv(USERS_FILE, index=False, encoding='utf-8-sig')
                            st.success("🗑️ تم حذف الحساب من السجلات بنجاح!")
                            st.rerun()

        with tab_roles:
            st.subheader("🔑 جدول التحكم التفاعلي بالصفحات")
            edited_perms_df = st.data_editor(perms_df, use_container_width=True, disabled=["اسم الصفحة"])
            if st.button("💾 حفظ الصلاحيات والتعديلات الجديدة"):
                edited_perms_df.to_csv(PERMISSIONS_FILE, index=False, encoding='utf-8-sig')
                st.success("🚀 تم تحديث قواعد الصلاحيات!")
                st.rerun()

    # --- 13. صفحة إعدادات بيانات الفاتورة والدعم ---
    elif "إعدادات بيانات الفاتورة والدعم" in choice:
        st.header("⚙️ تحديث وإعداد بيانات طباعة الفاتورة والدعم")
        with st.form("settings_form_updated"):
            new_showroom_name = st.text_input("اسم المعرض / الشركة بالفاتورة", value=SHOWROOM_NAME)
            new_showroom_address = st.text_input("العنوان بالتفصيل بالفاتورة", value=SHOWROOM_ADDRESS)
            new_inquiry_number = st.text_input("رقم الدعم الفني للفواتير", value=INQUIRY_NUMBER)
            if st.form_submit_button("💾 حفظ وتحديث الإعدادات"):
                updated_settings = pd.DataFrame([{"اسم المعرض": new_showroom_name, "العنوان": new_showroom_address, "رقم الدعم": new_inquiry_number}])
                updated_settings.to_csv(SETTINGS_FILE, index=False, encoding='utf-8-sig')
                st.success("🚀 تم تحديث بيانات الفاتورة بنجاح!")
                st.rerun()
