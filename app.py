import streamlit as st
import pandas as pd
import datetime
import sqlite3

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Better Nutrition ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE SETUP ---
def get_connection():
    conn = sqlite3.connect("better_nutrition_erp.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Raw Material Receiving Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT,
            vendor_name TEXT,
            material_name TEXT,
            miller_name TEXT,
            vehicle_number TEXT,
            po_number TEXT,
            invoice_number TEXT,
            gross_qty REAL,
            bag_type TEXT,
            total_bags INTEGER,
            bag_wt REAL,
            net_wt REAL,
            entered_by TEXT
        )
    """)
    
    # 2. Raw Material Quality Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_material_quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            hl REAL,
            foreign_material REAL,
            moisture REAL,
            visibility TEXT,
            entered_by TEXT
        )
    """)

    # 3. Milling Entry Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milling (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milling_date TEXT,
            miller_name TEXT,
            milling_qty REAL,
            material_type TEXT,
            batch_code TEXT,
            entered_by TEXT
        )
    """)

    # 4. Finished Goods Entry Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finished_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            production_date TEXT,
            miller_name TEXT,
            sku TEXT,
            mfd_date TEXT,
            use_by_date TEXT,
            mrp REAL,
            batch_number TEXT,
            qty INTEGER,
            drop_test TEXT,
            sealing TEXT,
            entered_by TEXT
        )
    """)

    # 5. Employees Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT,
            pin TEXT,
            role TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO employees (employee_name, pin, role) VALUES (?, ?, ?)", ("Admin", "1234", "Admin"))
        cursor.execute("INSERT INTO employees (employee_name, pin, role) VALUES (?, ?, ?)", ("Miller Team", "0000", "Team"))
    
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def load_data(table_name):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM raw_material WHERE 1=0", conn) if table_name == "raw_material" else pd.read_sql(f"SELECT * FROM {table_name}", conn)
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        pass
    conn.close()
    return df

def send_email_alert(subject, body):
    # Stub function for email alerting
    pass

def get_miller_input(key_prefix, default_val=None):
    conn = get_connection()
    df_emp = pd.read_sql("SELECT employee_name FROM employees", conn)
    conn.close()
    millers_list = df_emp["employee_name"].tolist() if not df_emp.empty else ["Default Miller"]
    
    idx = 0
    if default_val in millers_list:
        idx = millers_list.index(default_val)
    
    return st.selectbox("Miller Name", millers_list, index=idx, key=f"miller_sel_{key_prefix}")

# --- STYLING & THEME ---
st.markdown("""
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
""", unsafe_allow_html=True)

# --- SESSION STATE LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_name"] = ""
    st.session_state["user_role"] = ""

if not st.session_state["logged_in"]:
    st.markdown("""
        <div class="hero-banner" style="text-align: center;">
            <h1>🌾 Better Nutrition ERP</h1>
            <p>Please log in using your employee credentials</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            username = st.text_input("Employee Name")
            pin = st.text_input("4-Digit PIN", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM employees WHERE employee_name = ? AND pin = ?", (username.strip(), pin.strip()))
                res = cursor.fetchone()
                conn.close()
                if res:
                    st.session_state["logged_in"] = True
                    st.session_state["user_name"] = username.strip()
                    st.session_state["user_role"] = res[0]
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

menu = st.sidebar.radio("Navigation Menu", [
    "1. Raw Material Receiving",
    "2. Raw Material Quality Lab",
    "3. Milling Entry",
    "4. Finished Goods Entry",
    "5. Dashboards",
    "6. Master Records & Admin"
])

# ==========================================
# 1. RAW MATERIAL RECEIVING
# ==========================================
if menu == "1. Raw Material Receiving":
    st.markdown("""
        <div class="hero-banner">
            <h1>Incoming Raw Material Entry</h1>
            <p>Record incoming raw material loads, weights, bag counts, and supplier details.</p>
        </div>
    """, unsafe_allow_html=True)

    if "edit_rm_id" not in st.session_state:
        st.session_state["edit_rm_id"] = None

    df_rm_saved = load_data("raw_material")

    action_type_rm = "➕ New Raw Material Entry"
    if not df_rm_saved.empty:
        action_type_rm = st.radio("Action Mode", ["➕ New Raw Material Entry", "✏️ Edit / 🗑️ Delete Existing Record"], horizontal=True, key="mode_rm")
    else:
        action_type_rm = "➕ New Raw Material Entry"

    edit_rm_data = None
    if action_type_rm == "✏️ Edit / 🗑️ Delete Existing Record" and not df_rm_saved.empty:
        df_rm_saved["label"] = "ID: " + df_rm_saved["id"].astype(str) + " | Inv: " + df_rm_saved["invoice_number"].fillna("N/A") + " | Vendor: " + df_rm_saved["vendor_name"].fillna("N/A")
        sel_rm_lbl = st.selectbox("Select Record to Modify/Delete", df_rm_saved["label"].tolist(), key="sel_rm_mod")
        row_rm_edit = df_rm_saved[df_rm_saved["label"] == sel_rm_lbl].iloc[0]
        st.session_state["edit_rm_id"] = int(row_rm_edit["id"])
        edit_rm_data = row_rm_edit

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del_rm = st.checkbox("Haan, main is record ko permanently delete karna chahta hoon", key="conf_del_rm_rec")
            if st.button("🗑️ Confirm & Delete Record", type="primary", key="btn_del_rm_rec"):
                if confirm_del_rm:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM raw_material WHERE id = ?", (st.session_state["edit_rm_id"],))
                    conn.commit()
                    conn.close()
                    st.success("Record deleted successfully!")
                    st.session_state["edit_rm_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        if action_type_rm != "✏️ Edit / 🗑️ Delete Existing Record":
            st.session_state["edit_rm_id"] = None

    if action_type_rm == "➕ New Raw Material Entry" or st.session_state["edit_rm_id"] is not None:
        default_miller = edit_rm_data["miller_name"] if edit_rm_data is not None else None
        miller_name = get_miller_input("rm", default_miller)

        with st.form("raw_material_form"):
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                rm_date_val = datetime.date.today()
                if edit_rm_data is not None and pd.notnull(edit_rm_data["entry_date"]):
                    try:
                        rm_date_val = datetime.datetime.strptime(edit_rm_data["entry_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                rm_date_obj = st.date_input("Date", value=rm_date_val)
                entry_date = rm_date_obj.strftime("%d %b %Y")

                default_vendor = edit_rm_data["vendor_name"] if edit_rm_data is not None and pd.notnull(edit_rm_data["vendor_name"]) else ""
                vendor_name = st.text_input("Vendor Name", value=default_vendor)

                default_mat = edit_rm_data["material_name"] if edit_rm_data is not None and pd.notnull(edit_rm_data["material_name"]) else ""
                material_name = st.text_input("Material Name", value=default_mat, placeholder="e.g. Wheat")

            with rc2:
                default_veh = edit_rm_data["vehicle_number"] if edit_rm_data is not None and pd.notnull(edit_rm_data["vehicle_number"]) else ""
                vehicle_number = st.text_input("Vehicle Number", value=default_veh)

                default_po = edit_rm_data["po_number"] if edit_rm_data is not None and pd.notnull(edit_rm_data["po_number"]) else ""
                po_number = st.text_input("PO Number", value=default_po)

                default_inv = edit_rm_data["invoice_number"] if edit_rm_data is not None and pd.notnull(edit_rm_data["invoice_number"]) else ""
                invoice_number = st.text_input("Invoice Number", value=default_inv)

            with rc3:
                default_gross = float(edit_rm_data["gross_qty"]) if edit_rm_data is not None and pd.notnull(edit_rm_data["gross_qty"]) else 0.0
                gross_qty = st.number_input("Gross Qty", min_value=0.0, value=default_gross, step=50.0)

                bag_options = ["Jute Bag", "Plastic Bag"]
                default_bag_idx = 0
                if edit_rm_data is not None and edit_rm_data["bag_type"] in bag_options:
                    default_bag_idx = bag_options.index(edit_rm_data["bag_type"])
                bag_type = st.selectbox("Bag Type", bag_options, index=default_bag_idx)

                default_tot_bags = int(edit_rm_data["total_bags"]) if edit_rm_data is not None and pd.notnull(edit_rm_data["total_bags"]) else 0
                total_bags = st.number_input("Number Of Total Bags", min_value=0, value=default_tot_bags, step=10)

                default_bag_wt = float(edit_rm_data["bag_wt"]) if edit_rm_data is not None and pd.notnull(edit_rm_data["bag_wt"]) else 0.0
                bag_wt = st.number_input("Bag Wt", min_value=0.0, value=default_bag_wt, step=0.1)

            # Formula: Net Wt = Gross Qty - (Number Of total Bags * Bag Wt)
            net_wt = gross_qty - (total_bags * bag_wt)
            st.info(f"Calculated Net Wt (Gross Qty - [Total Bags * Bag Wt]): **{net_wt:,.2f}**")

            btn_label = "Update Record" if st.session_state["edit_rm_id"] is not None else "Save Raw Material Entry"
            submit_rm = st.form_submit_button(label=btn_label)

            if submit_rm:
                conn = get_connection()
                cursor = conn.cursor()
                if st.session_state["edit_rm_id"] is not None:
                    cursor.execute("""
                        UPDATE raw_material 
                        SET entry_date=?, vendor_name=?, material_name=?, miller_name=?, vehicle_number=?, po_number=?, invoice_number=?, gross_qty=?, bag_type=?, total_bags=?, bag_wt=?, net_wt=?
                        WHERE id=?
                    """, (entry_date, vendor_name, material_name, miller_name, vehicle_number, po_number, invoice_number, gross_qty, bag_type, total_bags, bag_wt, round(net_wt, 2), st.session_state["edit_rm_id"]))
                    conn.commit()
                    conn.close()
                    st.success("Raw Material Record Updated Successfully!")
                    st.session_state["edit_rm_id"] = None
                    st.rerun()
                else:
                    cursor.execute("""
                        INSERT INTO raw_material (entry_date, vendor_name, material_name, miller_name, vehicle_number, po_number, invoice_number, gross_qty, bag_type, total_bags, bag_wt, net_wt, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (entry_date, vendor_name, material_name, miller_name, vehicle_number, po_number, invoice_number, gross_qty, bag_type, total_bags, bag_wt, round(net_wt, 2), current_logged_user))
                    conn.commit()
                    conn.close()
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
    st.markdown("""
        <div class="hero-banner">
            <h1>Incoming Raw Material Quality Lab Testing</h1>
            <p>Track HL, Foreign Material, Moisture, and Visibility mapped to Incoming Raw Material Invoice Number.</p>
        </div>
    """, unsafe_allow_html=True)

    if "edit_rmq_id" not in st.session_state:
        st.session_state["edit_rmq_id"] = None

    df_rm_all = load_data("raw_material")
    df_rmq_saved = load_data("raw_material_quality")

    action_type_rmq = "➕ New Quality Entry"
    if not df_rmq_saved.empty:
        action_type_rmq = st.radio("Action Mode", ["➕ New Quality Entry", "✏️ Edit / 🗑️ Delete Existing Quality Record"], horizontal=True, key="mode_rmq")
    else:
        action_type_rmq = "➕ New Quality Entry"

    edit_rmq_data = None
    if action_type_rmq == "✏️ Edit / 🗑️ Delete Existing Quality Record" and not df_rmq_saved.empty:
        df_rmq_saved["label"] = "ID: " + df_rmq_saved["id"].astype(str) + " | Invoice: " + df_rmq_saved["invoice_number"].fillna("N/A")
        sel_rmq_lbl = st.selectbox("Select Quality Record to Modify/Delete", df_rmq_saved["label"].tolist(), key="sel_rmq_mod")
        row_rmq_edit = df_rmq_saved[df_rmq_saved["label"] == sel_rmq_lbl].iloc[0]
        st.session_state["edit_rmq_id"] = int(row_rmq_edit["id"])
        edit_rmq_data = row_rmq_edit

        with st.expander("⚠️ Delete Quality Confirmation Box", expanded=False):
            confirm_del_rmq = st.checkbox("Haan, main is quality record ko permanently delete karna chahta hoon", key="conf_del_rmq_rec")
            if st.button("🗑️ Confirm & Delete Quality Record", type="primary", key="btn_del_rmq_rec"):
                if confirm_del_rmq:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM raw_material_quality WHERE id = ?", (st.session_state["edit_rmq_id"],))
                    conn.commit()
                    conn.close()
                    st.success("Quality record deleted successfully!")
                    st.session_state["edit_rmq_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        if action_type_rmq != "✏️ Edit / 🗑️ Delete Existing Quality Record":
            st.session_state["edit_rmq_id"] = None

    if action_type_rmq == "➕ New Quality Entry" or st.session_state["edit_rmq_id"] is not None:
        if df_rm_all.empty:
            st.warning("Pehle Raw Material Receiving entry add karein, tabhi Quality entry track ho sakegi.")
        else:
            invoices = df_rm_all["invoice_number"].dropna().unique().tolist()
            default_inv_idx = 0
            if edit_rmq_data is not None and edit_rmq_data["invoice_number"] in invoices:
                default_inv_idx = invoices.index(edit_rmq_data["invoice_number"])

            with st.form("raw_material_quality_form"):
                invoice_number = st.selectbox("Select Incoming Raw Material Invoice Number", invoices, index=default_inv_idx)
                
                qc1, qc2 = st.columns(2)
                with qc1:
                    default_hl = float(edit_rmq_data["hl"]) if edit_rmq_data is not None and pd.notnull(edit_rmq_data["hl"]) else 0.0
                    hl = st.number_input("HL (Hectolitre Weight)", min_value=0.0, value=default_hl, step=0.1)

                    default_fm = float(edit_rmq_data["foreign_material"]) if edit_rmq_data is not None and pd.notnull(edit_rmq_data["foreign_material"]) else 0.0
                    foreign_material = st.number_input("Foreign Material %", min_value=0.0, value=default_fm, step=0.01, format="%.2f")

                with qc2:
                    default_mois = float(edit_rmq_data["moisture"]) if edit_rmq_data is not None and pd.notnull(edit_rmq_data["moisture"]) else 0.0
                    moisture = st.number_input("Moisture %", min_value=0.0, value=default_mois, step=0.1, format="%.1f")

                    default_vis = edit_rmq_data["visibility"] if edit_rmq_data is not None and pd.notnull(edit_rmq_data["visibility"]) else ""
                    visibility = st.text_input("Visibility / Grain Appearance", value=default_vis, placeholder="e.g. Clean / Clear")

                btn_q_label = "Update Quality Record" if st.session_state["edit_rmq_id"] is not None else "Save Quality Entry"
                submit_q = st.form_submit_button(label=btn_q_label)

                if submit_q:
                    conn = get_connection()
                    cursor = conn.cursor()
                    if st.session_state["edit_rmq_id"] is not None:
                        cursor.execute("""
                            UPDATE raw_material_quality 
                            SET invoice_number=?, hl=?, foreign_material=?, moisture=?, visibility=?
                            WHERE id=?
                        """, (invoice_number, hl, foreign_material, moisture, visibility, st.session_state["edit_rmq_id"]))
                        conn.commit()
                        conn.close()
                        st.success("Quality Record Updated Successfully!")
                        st.session_state["edit_rmq_id"] = None
                        st.rerun()
                    else:
                        cursor.execute("""
                            INSERT INTO raw_material_quality (invoice_number, hl, foreign_material, moisture, visibility, entered_by)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (invoice_number, hl, foreign_material, moisture, visibility, current_logged_user))
                        conn.commit()
                        conn.close()
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
    st.markdown("""
        <div class="hero-banner">
            <h1>Milling Processing Entry</h1>
            <p>Log milling details, material types, batch codes, and quantities processed by millers.</p>
        </div>
    """, unsafe_allow_html=True)

    if "edit_mil_id" not in st.session_state:
        st.session_state["edit_mil_id"] = None

    df_mil_saved = load_data("milling")

    action_type_mil = "➕ New Milling Entry"
    if not df_mil_saved.empty:
        action_type_mil = st.radio("Action Mode", ["➕ New Milling Entry", "✏️ Edit / 🗑️ Delete Existing Milling Record"], horizontal=True, key="mode_mil")
    else:
        action_type_mil = "➕ New Milling Entry"

    edit_mil_data = None
    if action_type_mil == "✏️ Edit / 🗑️ Delete Existing Milling Record" and not df_mil_saved.empty:
        df_mil_saved["label"] = "ID: " + df_mil_saved["id"].astype(str) + " | Date: " + df_mil_saved["milling_date"] + " | Batch: " + df_mil_saved["batch_code"].fillna("N/A")
        sel_mil_lbl = st.selectbox("Select Milling Record to Modify/Delete", df_mil_saved["label"].tolist(), key="sel_mil_mod")
        row_mil_edit = df_mil_saved[df_mil_saved["label"] == sel_mil_lbl].iloc[0]
        st.session_state["edit_mil_id"] = int(row_mil_edit["id"])
        edit_mil_data = row_mil_edit

        with st.expander("⚠️ Delete Milling Confirmation Box", expanded=False):
            confirm_del_mil = st.checkbox("Haan, main is milling record ko permanently delete karna chahta hoon", key="conf_del_mil_rec")
            if st.button("🗑️ Confirm & Delete Milling Record", type="primary", key="btn_del_mil_rec"):
                if confirm_del_mil:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM milling WHERE id = ?", (st.session_state["edit_mil_id"],))
                    conn.commit()
                    conn.close()
                    st.success("Milling record deleted successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        if action_type_mil != "✏️ Edit / 🗑️ Delete Existing Milling Record":
            st.session_state["edit_mil_id"] = None

    if action_type_mil == "➕ New Milling Entry" or st.session_state["edit_mil_id"] is not None:
        default_miller_mil = edit_mil_data["miller_name"] if edit_mil_data is not None else None
        miller = get_miller_input("milling", default_miller_mil)

        with st.form("milling_form"):
            mc1, mc2 = st.columns(2)
            with mc1:
                mil_date_val = datetime.date.today()
                if edit_mil_data is not None and pd.notnull(edit_mil_data["milling_date"]):
                    try:
                        mil_date_val = datetime.datetime.strptime(edit_mil_data["milling_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                mil_date_obj = st.date_input("Date", value=mil_date_val)
                milling_date = mil_date_obj.strftime("%d %b %Y")

                default_mqty = float(edit_mil_data["milling_qty"]) if edit_mil_data is not None and pd.notnull(edit_mil_data["milling_qty"]) else 0.0
                milling_qty = st.number_input("QTY (kg)", min_value=0.0, value=default_mqty, step=50.0)

            with mc2:
                default_mtype = edit_mil_data["material_type"] if edit_mil_data is not None and pd.notnull(edit_mil_data["material_type"]) else ""
                material_type = st.text_input("Material Type", value=default_mtype, placeholder="e.g. Wheat Atta Grind")

                default_batch = edit_mil_data["batch_code"] if edit_mil_data is not None and pd.notnull(edit_mil_data["batch_code"]) else ""
                batch_code = st.text_input("Batch Code of Milling", value=default_batch, placeholder="e.g. MILL-BATCH-01")

            btn_m_label = "Update Milling Record" if st.session_state["edit_mil_id"] is not None else "Save Milling Entry"
            submit_milling = st.form_submit_button(label=btn_m_label)

            if submit_milling:
                conn = get_connection()
                cursor = conn.cursor()
                if st.session_state["edit_mil_id"] is not None:
                    cursor.execute("""
                        UPDATE milling 
                        SET milling_date=?, miller_name=?, milling_qty=?, material_type=?, batch_code=?
                        WHERE id=?
                    """, (milling_date, miller, milling_qty, material_type, batch_code, st.session_state["edit_mil_id"]))
                    conn.commit()
                    conn.close()
                    st.success("Milling Record Updated Successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    cursor.execute("""
                        INSERT INTO milling (milling_date, miller_name, milling_qty, material_type, batch_code, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (milling_date, miller, milling_qty, material_type, batch_code, current_logged_user))
                    conn.commit()
                    conn.close()
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
    st.markdown("""
        <div class="hero-banner">
            <h1>Finished Goods Entry (SKU-wise Packets)</h1>
            <p>Log packaged production details for 500gm, 1kg, 2kg, and 5kg SKUs with testing parameters.</p>
        </div>
    """, unsafe_allow_html=True)

    if "edit_fg_id" not in st.session_state:
        st.session_state["edit_fg_id"] = None

    df_fg_saved = load_data("finished_goods")

    action_type_fg = "➕ New Finished Goods Entry"
    if not df_fg_saved.empty:
        action_type_fg = st.radio("Action Mode", ["➕ New Finished Goods Entry", "✏️ Edit / 🗑️ Delete Existing Finished Goods"], horizontal=True, key="mode_fg")
    else:
        action_type_fg = "➕ New Finished Goods Entry"

    edit_fg_data = None
    if action_type_fg == "✏️ Edit / 🗑️ Delete Existing Finished Goods" and not df_fg_saved.empty:
        df_fg_saved["label"] = "ID: " + df_fg_saved["id"].astype(str) + " | SKU: " + df_fg_saved["sku"].fillna("N/A") + " | Batch: " + df_fg_saved["batch_number"].fillna("N/A")
        sel_fg_lbl = st.selectbox("Select Finished Goods Record to Modify/Delete", df_fg_saved["label"].tolist(), key="sel_fg_mod")
        row_fg_edit = df_fg_saved[df_fg_saved["label"] == sel_fg_lbl].iloc[0]
        st.session_state["edit_fg_id"] = int(row_fg_edit["id"])
        edit_fg_data = row_fg_edit

        with st.expander("⚠️ Delete Finished Goods Confirmation Box", expanded=False):
            confirm_del_fg = st.checkbox("Haan, main is finished goods record ko permanently delete karna chahta hoon", key="conf_del_fg_rec")
            if st.button("🗑️ Confirm & Delete Finished Goods", type="primary", key="btn_del_fg_rec"):
                if confirm_del_fg:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM finished_goods WHERE id = ?", (st.session_state["edit_fg_id"],))
                    conn.commit()
                    conn.close()
                    st.success("Finished Goods record deleted successfully!")
                    st.session_state["edit_fg_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        if action_type_fg != "✏️ Edit / 🗑️ Delete Existing Finished Goods":
            st.session_state["edit_fg_id"] = None

    if action_type_fg == "➕ New Finished Goods Entry" or st.session_state["edit_fg_id"] is not None:
        default_miller_fg = edit_fg_data["miller_name"] if edit_fg_data is not None else None
        miller_name = get_miller_input("fg", default_miller_fg)

        sku_options = ["Sku 500gm", "Sku 1kg", "Sku 2kg", "Sku 5kg"]
        default_sku_idx = 0
        if edit_fg_data is not None and edit_fg_data["sku"] in sku_options:
            default_sku_idx = sku_options.index(edit_fg_data["sku"])

        with st.form("finished_goods_form"):
            sku = st.selectbox("Select SKU", sku_options, index=default_sku_idx)
            
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                prod_date_val = datetime.date.today()
                if edit_fg_data is not None and pd.notnull(edit_fg_data["production_date"]):
                    try:
                        prod_date_val = datetime.datetime.strptime(edit_fg_data["production_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                prod_obj = st.date_input("Date", value=prod_date_val)
                production_date = prod_obj.strftime("%d %b %Y")

                mfd_val = datetime.date.today()
                if edit_fg_data is not None and pd.notnull(edit_fg_data["mfd_date"]):
                    try:
                        mfd_val = datetime.datetime.strptime(edit_fg_data["mfd_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                mfd_obj = st.date_input("MFD", value=mfd_val)
                mfd_date = mfd_obj.strftime("%d %b %Y")

                use_val = datetime.date.today() + datetime.timedelta(days=90)
                if edit_fg_data is not None and pd.notnull(edit_fg_data["use_by_date"]):
                    try:
                        use_val = datetime.datetime.strptime(edit_fg_data["use_by_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                use_obj = st.date_input("Use BY", value=use_val)
                use_by_date = use_obj.strftime("%d %b %Y")

            with fc2:
                default_mrp = float(edit_fg_data["mrp"]) if edit_fg_data is not None and pd.notnull(edit_fg_data["mrp"]) else 0.0
                mrp = st.number_input("MRP (₹)", min_value=0.0, value=default_mrp, step=10.0)

                default_batch = edit_fg_data["batch_number"] if edit_fg_data is not None and pd.notnull(edit_fg_data["batch_number"]) else ""
                batch_number = st.text_input("Batch Number", value=default_batch)

                default_qty = int(edit_fg_data["qty"]) if edit_fg_data is not None and pd.notnull(edit_fg_data["qty"]) else 0
                qty = st.number_input("QTY (Units / Pouches)", min_value=0, value=default_qty, step=10)

            with fc3:
                default_drop = edit_fg_data["drop_test"] if edit_fg_data is not None and pd.notnull(edit_fg_data["drop_test"]) else ""
                drop_test = st.text_input("Drop Test", value=default_drop, placeholder="e.g. Pass / Fail")

                default_sealing = edit_fg_data["sealing"] if edit_fg_data is not None and pd.notnull(edit_fg_data["sealing"]) else ""
                sealing = st.text_input("Sealing", value=default_sealing, placeholder="e.g. Excellent / Good")

            btn_fg_label = "Update Finished Goods Record" if st.session_state["edit_fg_id"] is not None else "Save Finished Goods Entry"
            submit_fg = st.form_submit_button(label=btn_fg_label)

            if submit_fg:
                conn = get_connection()
                cursor = conn.cursor()
                if st.session_state["edit_fg_id"] is not None:
                    cursor.execute("""
                        UPDATE finished_goods 
                        SET production_date=?, miller_name=?, sku=?, mfd_date=?, use_by_date=?, mrp=?, batch_number=?, qty=?, drop_test=?, sealing=?
                        WHERE id=?
                    """, (production_date, miller_name, sku, mfd_date, use_by_date, mrp, batch_number, qty, drop_test, sealing, st.session_state["edit_fg_id"]))
                    conn.commit()
                    conn.close()
                    st.success("Finished Goods Record Updated Successfully!")
                    st.session_state["edit_fg_id"] = None
                    st.rerun()
                else:
                    cursor.execute("""
                        INSERT INTO finished_goods (production_date, miller_name, sku, mfd_date, use_by_date, mrp, batch_number, qty, drop_test, sealing, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (production_date, miller_name, sku, mfd_date, use_by_date, mrp, batch_number, qty, drop_test, sealing, current_logged_user))
                    conn.commit()
                    conn.close()
                    st.success("Finished Goods Entry Saved Successfully!")
                    st.rerun()

    st.divider()
    st.subheader("Saved Finished Goods Entries")
    df_fg_disp = load_data("finished_goods")
    if not df_fg_disp.empty:
        st.dataframe(df_fg_disp, use_container_width=True)

# ==========================================
# 5. DASHBOARDS
# ==========================================
elif menu == "5. Dashboards":
    st.markdown("""
        <div class="hero-banner">
            <h1>ERP Analytical Dashboards</h1>
            <p>View Raw Material, Milling, Finished Goods, and Quality insights filtered by Miller and Date/Month.</p>
        </div>
    """, unsafe_allow_html=True)

    dash_tab1, dash_tab2, dash_tab3, dash_tab4 = st.tabs([
        "📦 Raw Material Receiving",
        "⚙️ Milling Material Dashboard",
        "🏭 Finished Good Dashboard",
        "🧪 Quality Dashboard"
    ])

    # --- TAB 1: Raw Material Receiving (Miller Wise, Month Wise) ---
    with dash_tab1:
        st.subheader("Raw Material Receiving Dashboard (Miller & Month Wise)")
        df_rm = load_data("raw_material")
        if df_rm.empty:
            st.info("No raw material records available.")
        else:
            # Extract Month for filtering
            def extract_month(date_str):
                try:
                    dt = datetime.datetime.strptime(str(date_str), "%d %b %Y")
                    return dt.strftime("%B %Y")
                except Exception:
                    return "Unknown"

            df_rm["month_year"] = df_rm["entry_date"].apply(extract_month)

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                all_millers = ["All"] + df_rm["miller_name"].dropna().unique().tolist()
                sel_miller_rm = st.selectbox("Filter by Miller", all_millers, key="dash_rm_miller")
            with col_f2:
                all_months = ["All"] + df_rm["month_year"].unique().tolist()
                sel_month_rm = st.selectbox("Filter by Month", all_months, key="dash_rm_month")

            df_filtered_rm = df_rm.copy()
            if sel_miller_rm != "All":
                df_filtered_rm = df_filtered_rm[df_filtered_rm["miller_name"] == sel_miller_rm]
            if sel_month_rm != "All":
                df_filtered_rm = df_filtered_rm[df_filtered_rm["month_year"] == sel_month_rm]

            st.metric("Total Net Weight Received (kg)", f"{df_filtered_rm['net_wt'].sum():,.2f}")
            st.metric("Total Bags Received", f"{df_filtered_rm['total_bags'].sum():,}")
            st.dataframe(df_filtered_rm.drop(columns=["month_year"], errors="ignore"), use_container_width=True)

    # --- TAB 2: Milling Material Dashboard (Miller Wise, Date Wise with all milling details) ---
    with dash_tab2:
        st.subheader("Milling Material Dashboard (Miller & Date Wise)")
        df_mil = load_data("milling")
        if df_mil.empty:
            st.info("No milling records available.")
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                all_millers_mil = ["All"] + df_mil["miller_name"].dropna().unique().tolist()
                sel_miller_mil = st.selectbox("Filter by Miller", all_millers_mil, key="dash_mil_miller")
            with col_f2:
                all_dates_mil = ["All"] + df_mil["milling_date"].dropna().unique().tolist()
                sel_date_mil = st.selectbox("Filter by Date", all_dates_mil, key="dash_mil_date")

            df_filtered_mil = df_mil.copy()
            if sel_miller_mil != "All":
                df_filtered_mil = df_filtered_mil[df_filtered_mil["miller_name"] == sel_miller_mil]
            if sel_date_mil != "All":
                df_filtered_mil = df_filtered_mil[df_filtered_mil["milling_date"] == sel_date_mil]

            st.metric("Total Milling Qty Processed (kg)", f"{df_filtered_mil['milling_qty'].sum():,.2f}")
            st.dataframe(df_filtered_mil, use_container_width=True)

    # --- TAB 3: Finished Good Dashboard (Miller Wise, Date Wise with all finished good details) ---
    with dash_tab3:
        st.subheader("Finished Good Dashboard (Miller & Date Wise)")
        df_fg = load_data("finished_goods")
        if df_fg.empty:
            st.info("No finished goods records available.")
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                all_millers_fg = ["All"] + df_fg["miller_name"].dropna().unique().tolist()
                sel_miller_fg = st.selectbox("Filter by Miller", all_millers_fg, key="dash_fg_miller")
            with col_f2:
                all_dates_fg = ["All"] + df_fg["production_date"].dropna().unique().tolist()
                sel_date_fg = st.selectbox("Filter by Date", all_dates_fg, key="dash_fg_date")

            df_filtered_fg = df_fg.copy()
            if sel_miller_fg != "All":
                df_filtered_fg = df_filtered_fg[df_filtered_fg["miller_name"] == sel_miller_fg]
            if sel_date_fg != "All":
                df_filtered_fg = df_filtered_fg[df_filtered_fg["production_date"] == sel_date_fg]

            st.metric("Total Finished Units Produced", f"{df_filtered_fg['qty'].sum():,}")
            st.dataframe(df_filtered_fg, use_container_width=True)

    # --- TAB 4: Quality Dashboard (Batch wise only) ---
    with dash_tab4:
        st.subheader("Quality Lab Dashboard (Batch Wise)")
        df_rmq = load_data("raw_material_quality")
        if df_rmq.empty:
            st.info("No quality records available.")
        else:
            all_invoices = ["All"] + df_rmq["invoice_number"].dropna().unique().tolist()
            sel_inv_q = st.selectbox("Filter by Invoice / Batch Number", all_invoices, key="dash_q_invoice")

            df_filtered_q = df_rmq.copy()
            if sel_inv_q != "All":
                df_filtered_q = df_filtered_q[df_filtered_q["invoice_number"] == sel_inv_q]

            st.dataframe(df_filtered_q, use_container_width=True)

# ==========================================
# 6. MASTER RECORDS & ADMIN
# ==========================================
elif menu == "6. Master Records & Admin":
    st.markdown("""
        <div class="hero-banner">
            <h1>Master Records & Admin Controls</h1>
            <p>Manage employee credentials, view full database tables, and export data.</p>
        </div>
    """, unsafe_allow_html=True)

    if user_role != "Admin":
        st.warning("⚠️ Yeh section sirf Admin ke liye restricted hai.")
    else:
        st.subheader("Employee PIN Management")
        conn_emp = get_connection()
        df_emp = pd.read_sql("SELECT * FROM employees", conn_emp)
        conn_emp.close()
        st.dataframe(df_emp, use_container_width=True)

        with st.form("add_emp_form"):
            st.write("### Add New Employee / Team Member")
            new_name = st.text_input("Employee Name")
            new_pin = st.text_input("4-Digit PIN", type="password")
            new_role = st.selectbox("Role", ["Team", "Admin"])
            sub_emp = st.form_submit_button("Add Employee")
            if sub_emp:
                if new_name and new_pin:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO employees (employee_name, pin, role) VALUES (?, ?, ?)", (new_name.strip(), new_pin.strip(), new_role))
                    conn.commit()
                    conn.close()
                    st.success(f"Employee {new_name} added successfully!")
                    st.rerun()
                else:
                    st.error("Name aur PIN dono bharna zaroori hai!")

        st.divider()
        st.subheader("Full Database Viewer")
        table_to_view = st.selectbox("Select Table to Inspect", ["raw_material", "raw_material_quality", "milling", "finished_goods", "employees"])
        df_view = load_data(table_to_view)
        st.dataframe(df_view, use_container_width=True)
