import datetime
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Better Nutrition ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- GOOGLE SHEETS CONNECTION SETUP ---
@st.cache_resource
def init_connection():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
        "universe_domain": st.secrets["gcp_service_account"].get("universe_domain", "googleapis.com")
    }

    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1SfRrw4a6uDn8XL6EaKHvMkmcXiUeOzbb89vIuzA0lg")

gc = init_connection()

# --- HELPER FUNCTIONS FOR GOOGLE SHEETS ---
def load_data(table_name):
    try:
        worksheet = gc.worksheet(table_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()

def insert_data(table_name, data_dict):
    try:
        worksheet = gc.worksheet(table_name)
    except Exception:
        headers = list(data_dict.keys())
        worksheet = gc.add_worksheet(title=table_name, rows="1000", cols=str(len(headers)))
        worksheet.append_row(headers)
    
    headers = worksheet.row_values(1)
    if not headers:
        headers = list(data_dict.keys())
        worksheet.append_row(headers)
        
    row_values = [data_dict.get(h, "") for h in headers]
    worksheet.append_row(row_values)

def get_miller_input(key_prefix, default_val=None):
    df_emp = load_data("employees")
    millers_list = (
        df_emp["employee_name"].tolist()
        if not df_emp.empty and "employee_name" in df_emp.columns
        else ["Admin", "Miller Team"]
    )

    idx = 0
    if default_val in millers_list:
        idx = millers_list.index(default_val)

    return st.selectbox(
        "Miller Name", millers_list, index=idx, key=f"miller_sel_{key_prefix}"
    )


# --- STYLING & THEME ---
st.markdown(
    """
    <style>
    .hero-banner {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
    }
    .hero-banner h1 {
        font-size: 2.2rem;
        margin-bottom: 5px;
    }
    .hero-banner p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE LOGIN CHECK ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""

if not st.session_state["logged_in"]:
    st.markdown(
        """
            <div class="hero-banner" style="text-align: center;">
                <h1>🌾 Better Nutrition ERP</h1>
                <p>Please log in using your employee credentials</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            username = st.text_input("Employee Name")
            pin = st.text_input("4-Digit PIN", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                df_emp = load_data("employees")
                res = None
                if not df_emp.empty:
                    df_emp["employee_name"] = df_emp["employee_name"].astype(str)
                    df_emp["pin"] = df_emp["pin"].astype(str)
                    
                    matched = df_emp[
                        (df_emp["employee_name"] == username.strip())
                        & (df_emp["pin"] == pin.strip())
                    ]
                    if not matched.empty:
                        res = matched.iloc[0]["role"]

                if res:
                    st.session_state["logged_in"] = True
                    st.session_state["user_name"] = username.strip()
                    st.session_state["user_role"] = res
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Employee Name or PIN!")
    st.stop()

current_logged_user = st.session_state["user_name"]
user_role = st.session_state["user_role"]

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown(f"### 👤 Logged In: **{current_logged_user}**")
st.sidebar.markdown(f"Role: **{user_role}**")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_name"] = ""
    st.session_state["user_role"] = ""
    st.rerun()

st.sidebar.divider()

menu = st.sidebar.radio(
    "Navigation Menu",
    [
        "1. Raw Material Receiving",
        "2. Raw Material Quality Lab",
        "3. Milling Entry",
        "4. Finished Goods Entry",
        "5. Dashboards & Stock Ledger",
        "6. Master Records & Admin",
    ],
)

# ==========================================
# 1. RAW MATERIAL RECEIVING
# ==========================================
if menu == "1. Raw Material Receiving":
    st.markdown(
        """
            <div class="hero-banner">
                <h1>Incoming Raw Material Entry</h1>
                <p>Record incoming raw material loads, weights, bag counts, and supplier details.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    miller_name = get_miller_input("rm")

    with st.form("raw_material_form"):
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            rm_date_obj = st.date_input("Date", value=datetime.date.today())
            entry_date = rm_date_obj.strftime("%d %b %Y")
            vendor_name = st.text_input("Vendor Name *")
            material_name = st.text_input(
                "Material Name *", placeholder="e.g. Wheat"
            )

        with rc2:
            vehicle_number = st.text_input("Vehicle Number *")
            po_number = st.text_input("PO Number *")
            invoice_number = st.text_input("Invoice Number *")

        with rc3:
            gross_qty = st.number_input(
                "Gross Qty *", value=None, step=50.0, placeholder="Type..."
            )
            bag_type = st.selectbox("Bag Type", ["Jute Bag", "Plastic Bag"])
            total_bags = st.number_input(
                "Number Of Total Bags *", value=None, step=10, placeholder="Type..."
            )
            bag_wt = st.number_input(
                "Bag Wt *", value=None, step=0.1, placeholder="Type..."
            )

        if (
            gross_qty is not None
            and total_bags is not None
            and bag_wt is not None
        ):
            net_wt = gross_qty - (total_bags * bag_wt)
            st.info(
                f"Calculated Net Wt (Gross Qty - [Total Bags * Bag Wt]):"
                f" **{net_wt:,.2f}**"
            )
        else:
            net_wt = 0.0

        submit_rm = st.form_submit_button(label="Save Raw Material Entry")

        if submit_rm:
            if (
                not vendor_name.strip()
                or not material_name.strip()
                or not vehicle_number.strip()
                or not po_number.strip()
                or not invoice_number.strip()
                or gross_qty is None
                or total_bags is None
                or bag_wt is None
            ):
                st.error("⚠️ कृपया सभी अनिवार्य (Mandatory) फील्ड्स सही से भरें!")
            else:
                data = {
                    "entry_date": entry_date,
                    "vendor_name": vendor_name.strip(),
                    "material_name": material_name.strip(),
                    "miller_name": miller_name,
                    "vehicle_number": vehicle_number.strip(),
                    "po_number": po_number.strip(),
                    "invoice_number": invoice_number.strip(),
                    "gross_qty": float(gross_qty),
                    "bag_type": bag_type,
                    "total_bags": int(total_bags),
                    "bag_wt": float(bag_wt),
                    "net_wt": round(float(net_wt), 2),
                    "entered_by": current_logged_user,
                }
                insert_data("raw_material", data)
                st.success("Raw Material Entry Saved Successfully!")
                st.rerun()

    st.divider()
    st.subheader("Saved Raw Material Records")
    df_rm_disp = load_data("raw_material")
    if not df_rm_disp.empty:
        st.dataframe(df_rm_disp, use_container_width=True)

# ==========================================
# 2. RAW MATERIAL QUALITY ENTRY
# ==========================================
elif menu == "2. Raw Material Quality Lab":
    st.markdown(
        """
            <div class="hero-banner">
                <h1>Incoming Raw Material Quality Lab Testing</h1>
                <p>Track HL, Foreign Material, Moisture, and Visibility mapped to Incoming Raw Material Invoice Number.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    df_rm_all = load_data("raw_material")

    if df_rm_all.empty or "invoice_number" not in df_rm_all.columns:
        st.warning(
            "Pehle Raw Material Receiving entry add karein, tabhi Quality entry"
            " track ho sakegi."
        )
    else:
        invoices = df_rm_all["invoice_number"].dropna().unique().tolist()

        with st.form("raw_material_quality_form"):
            invoice_number = st.selectbox(
                "Select Incoming Raw Material Invoice Number", invoices
            )

            qc1, qc2 = st.columns(2)
            with qc1:
                hl = st.number_input(
                    "HL (Hectolitre Weight) *",
                    value=None,
                    step=0.1,
                    placeholder="Type...",
                )
                foreign_material = st.number_input(
                    "Foreign Material % *",
                    value=None,
                    step=0.01,
                    format="%.2f",
                    placeholder="Type...",
                )

            with qc2:
                moisture = st.number_input(
                    "Moisture % *",
                    value=None,
                    step=0.1,
                    format="%.1f",
                    placeholder="Type...",
                )
                visibility = st.text_input(
                    "Visibility / Grain Appearance *", placeholder="e.g. Clean / Clear"
                )

            submit_q = st.form_submit_button(label="Save Quality Entry")

            if submit_q:
                if (
                    hl is None
                    or foreign_material is None
                    or moisture is None
                    or not visibility.strip()
                ):
                    st.error("⚠️ कृपया सभी क्वालिटी पैरामीटर भरना अनिवार्य है!")
                else:
                    data = {
                        "invoice_number": str(invoice_number),
                        "hl": float(hl),
                        "foreign_material": float(foreign_material),
                        "moisture": float(moisture),
                        "visibility": visibility.strip(),
                        "entered_by": current_logged_user,
                    }
                    insert_data("raw_material_quality", data)
                    st.success("Quality Entry Saved Successfully!")
                    st.rerun()

    st.divider()
    st.subheader("Saved Raw Material Quality Records")
    df_rmq_disp = load_data("raw_material_quality")
    if not df_rmq_disp.empty:
        st.dataframe(df_rmq_disp, use_container_width=True)

# ==========================================
# 3. MILLING ENTRY
# ==========================================
elif menu == "3. Milling Entry":
    st.markdown(
        """
            <div class="hero-banner">
                <h1>Milling Processing Entry</h1>
                <p>Log milling details, material types, batch codes, and quantities processed by millers.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    miller = get_miller_input("milling")

    with st.form("milling_form"):
        mc1, mc2 = st.columns(2)
        with mc1:
            mil_date_obj = st.date_input("Date", value=datetime.date.today())
            milling_date = mil_date_obj.strftime("%d %b %Y")
            milling_qty = st.number_input(
                "QTY (kg) *", value=None, step=50.0, placeholder="Type..."
            )

        with mc2:
            material_type = st.text_input(
                "Material Type *", placeholder="e.g. Wheat Atta Grind"
            )
            batch_code = st.text_input(
                "Batch Code of Milling *", placeholder="e.g. MILL-BATCH-01"
            )

        submit_milling = st.form_submit_button(label="Save Milling Entry")

        if submit_milling:
            if (
                not material_type.strip()
                or not batch_code.strip()
                or milling_qty is None
            ):
                st.error("⚠️ कृपया Material Type, Batch Code और Qty सही से भरें!")
            else:
                data = {
                    "milling_date": milling_date,
                    "miller_name": miller,
                    "milling_qty": float(milling_qty),
                    "material_type": material_type.strip(),
                    "batch_code": batch_code.strip(),
                    "entered_by": current_logged_user,
                }
                insert_data("milling", data)
                st.success("Milling Entry Saved Successfully!")
                st.rerun()

    st.divider()
    st.subheader("Saved Milling Records")
    df_mil_disp = load_data("milling")
    if not df_mil_disp.empty:
        st.dataframe(df_mil_disp, use_container_width=True)

# ==========================================
# 4. FINISHED GOODS ENTRY
# ==========================================
elif menu == "4. Finished Goods Entry":
    st.markdown(
        """
            <div class="hero-banner">
                <h1>Finished Goods Entry (SKU-wise Packets)</h1>
                <p>Log packaged production details for SKUs with testing parameters.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    miller_name = get_miller_input("fg")
    sku_options = ["Sku 500gm", "Sku 1kg", "Sku 2kg", "Sku 5kg"]

    with st.form("finished_goods_form"):
        sku = st.selectbox("Select SKU", sku_options)

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            prod_obj = st.date_input("Production Date", value=datetime.date.today())
            production_date = prod_obj.strftime("%d %b %Y")
            mfd_obj = st.date_input("MFD Date", value=datetime.date.today())
            mfd_date = mfd_obj.strftime("%d %b %Y")
            use_obj = st.date_input(
                "Use BY Date", value=datetime.date.today() + datetime.timedelta(days=90)
            )
            use_by_date = use_obj.strftime("%d %b %Y")

        with fc2:
            mrp = st.number_input(
                "MRP *", value=None, step=1.0, placeholder="Type..."
            )
            batch_number = st.text_input("Batch Number *")
            qty = st.number_input(
                "Quantity (Packets) *", value=None, step=10, placeholder="Type..."
            )

        with fc3:
            drop_test = st.selectbox("Drop Test Status", ["Pass", "Fail"])
            sealing = st.selectbox("Sealing Quality", ["Good", "Average", "Bad"])

        submit_fg = st.form_submit_button(label="Save Finished Goods Entry")

        if submit_fg:
            if mrp is None or not batch_number.strip() or qty is None:
                st.error("⚠️ कृपया MRP, Batch Number और Quantity सही से भरें!")
            else:
                data = {
                    "production_date": production_date,
                    "miller_name": miller_name,
                    "sku": sku,
                    "mfd_date": mfd_date,
                    "use_by_date": use_by_date,
                    "mrp": float(mrp),
                    "batch_number": batch_number.strip(),
                    "qty": int(qty),
                    "drop_test": drop_test,
                    "sealing": sealing,
                    "entered_by": current_logged_user,
                }
                insert_data("finished_goods", data)
                st.success("Finished Goods Entry Saved Successfully!")
                st.rerun()

    st.divider()
    st.subheader("Saved Finished Goods Inventory")
    df_fg_disp = load_data("finished_goods")
    if not df_fg_disp.empty:
        st.dataframe(df_fg_disp, use_container_width=True)

# ==========================================
# 5. DASHBOARDS & STOCK LEDGER
# ==========================================
elif menu == "5. Dashboards & Stock Ledger":
    st.markdown(
        """
            <div class="hero-banner">
                <h1>Executive Dashboards & Stock Ledger</h1>
                <p>Overview of all inventory entries, raw material processing, and finished goods stock.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    rm_df = load_data("raw_material")
    fg_df = load_data("finished_goods")

    with col1:
        st.metric(label="Total Raw Material Entries", value=len(rm_df))
    with col2:
        st.metric(label="Total Finished Goods Entries", value=len(fg_df))

    st.subheader("📦 Raw Material Ledger")
    if not rm_df.empty:
        st.dataframe(rm_df, use_container_width=True)
    else:
        st.info("No raw material records found.")

    st.subheader("📦 Finished Goods Ledger")
    if not fg_df.empty:
        st.dataframe(fg_df, use_container_width=True)
    else:
        st.info("No finished goods records found.")

# ==========================================
# 6. MASTER RECORDS & ADMIN
# ==========================================
elif menu == "6. Master Records & Admin":
    st.markdown(
        """
            <div class="hero-banner">
                <h1>Master Records & Administration</h1>
                <p>Manage system users, employees, and roles.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("👥 Employee Directory")
    df_emp = load_data("employees")
    if not df_emp.empty:
        if "pin" in df_emp.columns:
            df_emp_safe = df_emp.drop(columns=["pin"])
        else:
            df_emp_safe = df_emp
        st.dataframe(df_emp_safe, use_container_width=True)
    else:
        st.info("No employees found.")

    if user_role == "Admin":
        st.divider()
        st.subheader("➕ Add New Employee")
        with st.form("add_emp_form"):
            new_emp_name = st.text_input("Employee Name *")
            new_pin = st.text_input("4-Digit PIN *", type="password")
            new_role = st.selectbox("Role", ["Admin", "Team"])

            sub_emp = st.form_submit_button("Create Employee")

            if sub_emp:
                if not new_emp_name.strip() or not new_pin.strip():
                    st.error("⚠️ कृपया Employee Name और 4-Digit PIN दोनों भरें।")
                else:
                    data = {
                        "employee_name": new_emp_name.strip(),
                        "pin": str(new_pin.strip()),
                        "role": new_role,
                    }
                    insert_data("employees", data)
                    st.success("Employee added successfully!")
                    st.rerun()
    else:
        st.info("🔒 Admin actions are restricted to Admin role users only.")
