import datetime
import os
import smtplib
from email.message import EmailMessage
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Better Nutrition & Flour Mill ERP", layout="wide"
)

# Custom CSS for Modern UI Layout
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0px;
        border-bottom: 1px solid #E5E7EB;
        margin-bottom: 20px;
    }
    .hero-banner {
        background: linear-gradient(135deg, #0A2F1D 0%, #134E2D 100%);
        color: white;
        padding: 25px 30px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    .hero-banner h1 {
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 5px;
        color: #FFFFFF;
    }
    .hero-banner p {
        font-size: 14px;
        color: #D1D5DB;
        margin: 0;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""",
    unsafe_allow_html=True,
)


def get_connection():
    return sqlite3.connect("flour_mill_erp.db", check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT, rm_date TEXT, miller_name TEXT, vendor_name TEXT, vehicle_number TEXT, hectoliter_weight REAL, moisture_rm REAL, broken_pct REAL, infestation TEXT, jute_bags INTEGER, gross_qty REAL, jute_weight REAL, net_weight REAL, remarks TEXT, entered_by TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milling (
            id INTEGER PRIMARY KEY AUTOINCREMENT, milling_date TEXT, miller_name TEXT, milling_qty REAL, tempering_time TEXT, tempering_water REAL, finished_qty REAL, entered_by TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT, milling_id INTEGER, test_date TEXT, miller_name TEXT, moisture_milled REAL, granulation TEXT, ccl4 TEXT, ash_aia REAL, alcoholic_acidity REAL, wap REAL, gluten TEXT, chapati_sensory TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finished_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT, production_date TEXT, miller_name TEXT, flour_qty REAL, bran_qty REAL, chokar_qty REAL, total_finished_qty REAL, remarks TEXT, entered_by TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packing_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT, entry_date TEXT, miller_name TEXT, bag_size TEXT, received_bags INTEGER, issued_bags INTEGER, balance_bags INTEGER, remarks TEXT, entered_by TEXT
        )
    """)
    # Updated Dispatch table with SKU breakdown columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatch (
            id INTEGER PRIMARY KEY AUTOINCREMENT, dispatch_date TEXT, miller_name TEXT, party_name TEXT, vehicle_number TEXT, bags_500g INTEGER, bags_1kg INTEGER, bags_2kg INTEGER, pouches_5kg INTEGER, other_qty REAL, total_dispatched_wt REAL, remarks TEXT, entered_by TEXT
        )
    """)

    # Safe Column Alter Migrations for existing DBs
    for col_query in [
        "ALTER TABLE quality ADD COLUMN wap REAL",
        "ALTER TABLE raw_material ADD COLUMN entered_by TEXT",
        "ALTER TABLE milling ADD COLUMN entered_by TEXT",
        "ALTER TABLE milling ADD COLUMN finished_qty REAL",
        "ALTER TABLE finished_goods ADD COLUMN entered_by TEXT",
        "ALTER TABLE packing_material ADD COLUMN entered_by TEXT",
        "ALTER TABLE dispatch ADD COLUMN entered_by TEXT",
        "ALTER TABLE dispatch ADD COLUMN bags_30kg INTEGER",
        "ALTER TABLE dispatch ADD COLUMN bags_10kg INTEGER",
        "ALTER TABLE dispatch ADD COLUMN pouches_5kg INTEGER",
        "ALTER TABLE dispatch ADD COLUMN other_qty REAL",
    ]:
        try:
            cursor.execute(col_query)
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT, employee_name TEXT, pin TEXT, role TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO employees (employee_name, pin, role) VALUES (?, ?, ?)",
            ("Yash Sharma", "8358", "Team"),
        )
        cursor.execute(
            "INSERT INTO employees (employee_name, pin, role) VALUES (?, ?, ?)",
            ("Dheerendra Bhaskar", "7549", "Team"),
        )
        cursor.execute(
            "INSERT INTO employees (employee_name, pin, role) VALUES (?, ?, ?)",
            ("Admin", "adMin@123", "Admin"),
        )
        conn.commit()

    conn.close()


init_db()


def send_email_alert(subject, body):
    try:
        sender_email = "kamtanath111@gmail.com"
        sender_password = "kmbdgdznfcrdrrdh"
        receiver_email = "kamtanath111@gmail.com"

        msg = EmailMessage()
        msg.set_content(body)
        msg.subject = subject
        msg.from_ = sender_email
        msg.to = receiver_email

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Email error: {e}")


def check_auth():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["role"] = ""

    if not st.session_state["logged_in"]:
        st.markdown(
            """
            <div class="hero-banner" style="text-align: center;">
                <h1>ERP Login Portal</h1>
                <p>Team Member apni ID aur 4-digit PIN daalein | Admin username 'Admin' aur password daalein.</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                emp_name_input = st.text_input("Username / Employee Name / ID")
                emp_pin = st.text_input("PIN / Password", type="password")
                submit_login = st.form_submit_button("Login Karein")

                if submit_login:
                    if (
                        emp_name_input.strip() == "Admin"
                        and emp_pin.strip() == "adMin@123"
                    ):
                        st.session_state["logged_in"] = True
                        st.session_state["user_name"] = "Rishabh Admin"
                        st.session_state["role"] = "Admin"
                        st.success("Swagat hai, Admin! Dashboard khul raha hai...")
                        st.rerun()
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT employee_name, role FROM employees WHERE employee_name = ? AND pin = ?",
                            (emp_name_input.strip(), emp_pin.strip()),
                        )
                        user = cursor.fetchone()
                        conn.close()

                        if user:
                            st.session_state["logged_in"] = True
                            st.session_state["user_name"] = user[0]
                            st.session_state["role"] = user[1]
                            st.success(
                                f"Swagat hai, {user[0]}! App khul rahi hai..."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Galat Username/ID ya Password! Dobara koshish"
                                " karein."
                            )
        return False
    return True


if not check_auth():
    st.stop()

st.markdown(
    """
    <div class="header-container">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background-color: #0A2F1D; color: white; padding: 10px 14px; border-radius: 10px; font-weight: bold; font-size: 18px;">BN</div>
            <div>
                <h2 style="margin: 0; font-size: 20px; color: #111827;">Better Nutrition</h2>
                <p style="margin: 0; font-size: 12px; color: #6B7280;">Internal Stock Movement, Receiving, Exceptions & Milling Production</p>
            </div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <span style="background-color: #E6F4EA; color: #137333; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">🟢 LIVE</span>
            <span style="border: 1px solid #D1D5DB; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; color: #374151;">User: {user}</span>
        </div>
    </div>
""".format(
        user=st.session_state["user_name"]
    ),
    unsafe_allow_html=True,
)

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.session_state["user_name"] = ""
    st.session_state["role"] = ""
    st.rerun()

user_role = st.session_state.get("role", "Team")
current_logged_user = st.session_state.get("user_name", "Unknown")
st.sidebar.write(
    f"Logged in as: **{current_logged_user}** ({user_role})"
)

BASE_MILLER_LIST = [
    "Shree Balram Agro",
    "IKON ORG.",
    "Sathvik Agro",
    "Satya Naraian Kesho",
    "Tara Grains",
    "Other",
]


def load_data(table_name):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


menu = st.sidebar.selectbox(
    "Navigation Menu",
    [
        "Month-wise Summary Dashboard",
        "1. Raw Material Received",
        "2. Milling & Quality Lab Entry",
        "3. Finished Goods & Yield",
        "4. Better Nutrition Packing Material",
        "5. Daily Dispatch Entry",
        "6. Master Records & Export (Admin Controls)",
    ],
)


def get_miller_input(unique_key, default_val=None):
    st.write("### Select Miller Details")
    idx = 0
    if default_val and default_val in BASE_MILLER_LIST:
        idx = BASE_MILLER_LIST.index(default_val)
    elif default_val and default_val not in BASE_MILLER_LIST:
        idx = len(BASE_MILLER_LIST) - 1

    selected_option = st.selectbox(
        "Miller Name",
        BASE_MILLER_LIST,
        index=idx,
        key=f"ms_{unique_key}",
    )
    final_miller_name = selected_option
    if selected_option == "Other":
        custom_input_val = (
            default_val
            if default_val and default_val not in BASE_MILLER_LIST
            else ""
        )
        custom_name = st.text_input(
            "Enter New Miller Name Here",
            value=custom_input_val,
            key=f"cs_{unique_key}",
        )
        if custom_name:
            final_miller_name = custom_name
        else:
            final_miller_name = "Other (Pending Name)"
    return final_miller_name


if menu == "Month-wise Summary Dashboard":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Executive Month-wise Summary & Stock Dashboard</h1>
            <p>Track net raw materials, milling progress, finished goods production, and dispatches in real-time.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    df_rm = load_data("raw_material")
    if df_rm.empty:
        st.info("Pehle kuch data entries karein tab dashboard show hoga.")
    else:
        df_rm["Parsed_Date"] = pd.to_datetime(df_rm["rm_date"], errors="coerce")
        df_rm["Month-Year"] = df_rm["Parsed_Date"].dt.strftime("%B %Y")
        selected_month = st.selectbox(
            "Filter by Month-Year",
            ["All"] + list(df_rm["Month-Year"].dropna().unique()),
        )
        unique_millers = list(df_rm["miller_name"].unique())
        selected_miller = st.selectbox(
            "Filter by Miller Name", ["All"] + unique_millers
        )

        f_rm = df_rm.copy()
        if selected_month != "All":
            f_rm = f_rm[f_rm["Month-Year"] == selected_month]
        if selected_miller != "All":
            f_rm = f_rm[f_rm["miller_name"] == selected_miller]
        tot_net_rm = f_rm["net_weight"].sum()

        df_mil = load_data("milling")
        if not df_mil.empty:
            df_mil["Parsed_Date"] = pd.to_datetime(
                df_mil["milling_date"], errors="coerce"
            )
            df_mil["Month-Year"] = df_mil["Parsed_Date"].dt.strftime("%B %Y")
        f_mil = df_mil.copy()
        if not f_mil.empty:
            if selected_month != "All":
                f_mil = f_mil[f_mil["Month-Year"] == selected_month]
            if selected_miller != "All":
                f_mil = f_mil[f_mil["miller_name"] == selected_miller]
        tot_milled = (
            f_mil["milling_qty"].sum() if not f_mil.empty else 0.0
        )

        df_fg = load_data("finished_goods")
        if not df_fg.empty:
            df_fg["Parsed_Date"] = pd.to_datetime(
                df_fg["production_date"], errors="coerce"
            )
            df_fg["Month-Year"] = df_fg["Parsed_Date"].dt.strftime("%B %Y")
        f_fg = df_fg.copy()
        if not f_fg.empty:
            if selected_month != "All":
                f_fg = f_fg[f_fg["Month-Year"] == selected_month]
            if selected_miller != "All":
                f_fg = f_fg[f_fg["miller_name"] == selected_miller]
        tot_finished = (
            f_fg["total_finished_qty"].sum() if not f_fg.empty else 0.0
        )

        df_disp = load_data("dispatch")
        if not df_disp.empty:
            df_disp["Parsed_Date"] = pd.to_datetime(
                df_disp["dispatch_date"], errors="coerce"
            )
            df_disp["Month-Year"] = df_disp["Parsed_Date"].dt.strftime("%B %Y")
        f_disp = df_disp.copy()
        if not f_disp.empty:
            if selected_month != "All":
                f_disp = f_disp[f_disp["Month-Year"] == selected_month]
            if selected_miller != "All":
                f_disp = f_disp[f_disp["miller_name"] == selected_miller]
        tot_dispatched = (
            f_disp["total_dispatched_wt"].sum()
            if not f_disp.empty
            else 0.0
        )

        rm_closing_stock = tot_net_rm - tot_milled
        fg_closing_stock = tot_finished - tot_dispatched

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total Net RM (kg)", f"{tot_net_rm:,.2f}")
        c2.metric("Total Milled (kg)", f"{tot_milled:,.2f}")
        c3.metric("RM Closing (kg)", f"{rm_closing_stock:,.2f}")
        c4.metric("Total Finished (kg)", f"{tot_finished:,.2f}")
        c5.metric("Total Dispatched (kg)", f"{tot_dispatched:,.2f}")
        c6.metric("FG Closing (kg)", f"{fg_closing_stock:,.2f}")

        st.divider()
        st.subheader("Raw Material Overview Table")
        cols_to_drop = [
            c for c in ["Month-Year", "Parsed_Date"] if c in f_rm.columns
        ]
        st.dataframe(
            f_rm.drop(columns=cols_to_drop),
            use_container_width=True,
        )

elif menu == "1. Raw Material Received":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Raw Material Received Entry</h1>
            <p>Log new grain arrivals, check moisture levels, bag weights, and track vehicle details.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "edit_rm_id" not in st.session_state:
        st.session_state["edit_rm_id"] = None

    df_rm_saved = load_data("raw_material")

    if not df_rm_saved.empty:
        action_type = st.radio(
            "Action Mode",
            ["➕ New Entry", "✏️ Edit / 🗑️ Delete Existing Entry"],
            horizontal=True,
            key="mode_rm",
        )
    else:
        action_type = "➕ New Entry"

    edit_data = None
    if (
        action_type == "✏️ Edit / 🗑️ Delete Existing Entry"
        and not df_rm_saved.empty
    ):
        df_rm_saved["label"] = (
            "ID: "
            + df_rm_saved["id"].astype(str)
            + " | Date: "
            + df_rm_saved["rm_date"]
            + " | Miller: "
            + df_rm_saved["miller_name"]
            + " | Net Wt: "
            + df_rm_saved["net_weight"].astype(str)
            + " kg"
        )
        selected_row_label = st.selectbox(
            "Select Raw Material Record to Modify/Delete",
            df_rm_saved["label"].tolist(),
            key="sel_rm_edit",
        )
        selected_row = df_rm_saved[
            df_rm_saved["label"] == selected_row_label
        ].iloc[0]
        st.session_state["edit_rm_id"] = int(selected_row["id"])
        edit_data = selected_row

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del = st.checkbox(
                "Haan, main is record ko permanently delete karna chahta hoon",
                key="conf_del_rm",
            )
            if st.button(
                "🗑️ Confirm & Delete Record",
                type="primary",
                key="btn_del_rm_rec",
            ):
                if confirm_del:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM raw_material WHERE id = ?",
                        (st.session_state["edit_rm_id"],),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Record ID {st.session_state['edit_rm_id']} successfully deleted!"
                    )
                    st.session_state["edit_rm_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        st.session_state["edit_rm_id"] = None

    if (
        action_type == "➕ New Entry"
        or st.session_state["edit_rm_id"] is not None
    ):
        default_miller = (
            edit_data["miller_name"] if edit_data is not None else None
        )
        miller_name = get_miller_input("rm", default_miller)

        with st.form("rm_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                default_date = datetime.date.today()
                if edit_data is not None:
                    try:
                        default_date = datetime.datetime.strptime(
                            edit_data["rm_date"], "%d %b %Y"
                        ).date()
                    except Exception:
                        pass
                raw_date_obj = st.date_input("RM Date", value=default_date)
                rm_date = raw_date_obj.strftime("%d %b %Y")

                default_vendor = (
                    edit_data["vendor_name"] if edit_data is not None else ""
                )
                vendor_name = st.text_input("Vendor Name", value=default_vendor)

                default_veh = (
                    edit_data["vehicle_number"] if edit_data is not None else ""
                )
                vehicle_no = st.text_input(
                    "Vehicle Number",
                    value=default_veh,
                    placeholder="e.g. UP-75-AT-5079",
                )
            with c2:
                default_hecto = (
                    float(edit_data["hectoliter_weight"])
                    if edit_data is not None
                    else 0.0
                )
                hecto_wt = st.number_input(
                    "Hectoliter Weight",
                    min_value=0.0,
                    value=default_hecto,
                    step=0.1,
                    format="%.1f",
                )

                default_mois = (
                    float(edit_data["moisture_rm"])
                    if edit_data is not None
                    else 0.0
                )
                moisture_rm = st.number_input(
                    "Moisture % (RM)",
                    min_value=0.0,
                    value=default_mois,
                    step=0.1,
                    format="%.1f",
                )

                default_broken = (
                    float(edit_data["broken_pct"])
                    if edit_data is not None
                    else 0.0
                )
                broken_pct = st.number_input(
                    "Broken %",
                    min_value=0.0,
                    value=default_broken,
                    step=0.1,
                    format="%.1f",
                )
            with c3:
                infestation_opts = ["Nil", "Low", "Medium", "High"]
                default_inf_idx = 0
                if (
                    edit_data is not None
                    and edit_data["infestation"] in infestation_opts
                ):
                    default_inf_idx = infestation_opts.index(
                        edit_data["infestation"]
                    )
                infestation = st.selectbox(
                    "Infestation", infestation_opts, index=default_inf_idx
                )

                default_bags = (
                    int(edit_data["jute_bags"]) if edit_data is not None else 0
                )
                jute_bags = st.number_input(
                    "Number of Jute Bags (650g fix)",
                    min_value=0,
                    value=default_bags,
                    step=1,
                )

                default_gross = (
                    float(edit_data["gross_qty"])
                    if edit_data is not None
                    else 0.0
                )
                gross_qty = st.number_input(
                    "Gross Qty (kg)",
                    min_value=0.0,
                    value=default_gross,
                    step=10.0,
                    format="%.2f",
                )

            default_rem = edit_data["remarks"] if edit_data is not None else ""
            remarks = st.text_input("Remarks", value=default_rem)

            btn_label = (
                "Update Raw Material Record"
                if st.session_state["edit_rm_id"] is not None
                else "Save Raw Material Entry"
            )
            submit_rm = st.form_submit_button(label=btn_label)

            if submit_rm:
                jute_wt = jute_bags * 0.650
                net_wt = gross_qty - jute_wt
                conn = get_connection()
                cursor = conn.cursor()

                if st.session_state["edit_rm_id"] is not None:
                    cursor.execute(
                        """
                        UPDATE raw_material 
                        SET rm_date=?, miller_name=?, vendor_name=?, vehicle_number=?, hectoliter_weight=?, moisture_rm=?, broken_pct=?, infestation=?, jute_bags=?, gross_qty=?, jute_weight=?, net_weight=?, remarks=?
                        WHERE id=?
                    """,
                        (
                            rm_date,
                            miller_name,
                            vendor_name,
                            vehicle_no,
                            hecto_wt,
                            moisture_rm,
                            broken_pct,
                            infestation,
                            jute_bags,
                            gross_qty,
                            round(jute_wt, 2),
                            round(net_wt, 2),
                            remarks,
                            st.session_state["edit_rm_id"],
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Raw Material Record ID {st.session_state['edit_rm_id']}"
                        " Updated Successfully!"
                    )
                    st.session_state["edit_rm_id"] = None
                    st.rerun()
                else:
                    cursor.execute(
                        """
                        INSERT INTO raw_material (rm_date, miller_name, vendor_name, vehicle_number, hectoliter_weight, moisture_rm, broken_pct, infestation, jute_bags, gross_qty, jute_weight, net_weight, remarks, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            rm_date,
                            miller_name,
                            vendor_name,
                            vehicle_no,
                            hecto_wt,
                            moisture_rm,
                            broken_pct,
                            infestation,
                            jute_bags,
                            gross_qty,
                            round(jute_wt, 2),
                            round(net_wt, 2),
                            remarks,
                            current_logged_user,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    email_subject = f"[REPORT] New Raw Material Entry - {miller_name}"
                    email_body = f"""
BETTER NUTRITION - RAW MATERIAL ENTRY REPORT
============================================
Neeche nayi Raw Material entry ki poori report di gayi hai:

• Entry Date: {rm_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}
• Vendor Name: {vendor_name}
• Vehicle Number: {vehicle_no}

QUALITY & WEIGHT PARAMETERS:
• Hectoliter Weight: {hecto_wt}
• Moisture % (RM): {moisture_rm}%
• Broken %: {broken_pct}%
• Infestation Level: {infestation}
• Total Jute Bags: {jute_bags} (650g/bag fix)
• Gross Quantity: {gross_qty:,.2f} kg
• Jute Bag Weight: {round(jute_wt, 2):,.2f} kg
• Net Weight: {round(net_wt, 2):,.2f} kg
• Remarks: {remarks}

============================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
                    send_email_alert(email_subject, email_body)
                    st.success(
                        f"RM Saved & Stored by {current_logged_user}! Net Weight:"
                        f" {net_wt:,.2f} kg. Email report sent to Admin."
                    )
                    st.rerun()

    st.subheader("Saved Raw Material Entries")
    df_rm_saved_display = load_data("raw_material")
    if not df_rm_saved_display.empty:
        st.dataframe(df_rm_saved_display, use_container_width=True)

elif menu == "2. Milling & Quality Lab Entry":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Milling Processing, Finished Goods & Quality Lab Entry</h1>
            <p>Record milling quantities, finished goods production, tempering parameters, and lab test results.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "edit_mil_id" not in st.session_state:
        st.session_state["edit_mil_id"] = None

    df_mil_saved = load_data("milling")

    action_type_mil = "➕ New Milling & Quality Entry"
    if not df_mil_saved.empty:
        action_type_mil = st.radio(
            "Action Mode",
            [
                "➕ New Milling & Quality Entry",
                "✏️ Edit / 🗑️ Delete Existing Milling",
                "🛠️ Update Quality for Old Batches",
            ],
            horizontal=True,
            key="mode_mil",
        )
    else:
        action_type_mil = st.radio(
            "Action Mode",
            ["➕ New Milling & Quality Entry", "🛠️ Update Quality for Old Batches"],
            horizontal=True,
            key="mode_mil_empty",
        )

    edit_mil_data = None
    if (
        action_type_mil == "✏️ Edit / 🗑️ Delete Existing Milling"
        and not df_mil_saved.empty
    ):
        df_mil_saved["label"] = (
            "ID: "
            + df_mil_saved["id"].astype(str)
            + " | "
            + df_mil_saved["miller_name"]
            + " ("
            + df_mil_saved["milling_date"]
            + ")"
        )
        sel_edit_mil = st.selectbox(
            "Select Milling Record to Modify/Delete",
            df_mil_saved["label"].tolist(),
            key="sel_mil_mod",
        )
        row_edit_mil = df_mil_saved[
            df_mil_saved["label"] == sel_edit_mil
        ].iloc[0]
        st.session_state["edit_mil_id"] = int(row_edit_mil["id"])
        edit_mil_data = row_edit_mil

        with st.expander("⚠️ Delete Milling Confirmation Box", expanded=False):
            confirm_del_mil = st.checkbox(
                "Haan, main is milling record aur isse juda quality record"
                " delete karna chahta hoon",
                key="conf_del_mil_rec",
            )
            if st.button(
                "🗑️ Confirm & Delete Milling",
                type="primary",
                key="btn_del_mil_rec",
            ):
                if confirm_del_mil:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM milling WHERE id = ?",
                        (st.session_state["edit_mil_id"],),
                    )
                    cursor.execute(
                        "DELETE FROM quality WHERE milling_id = ?",
                        (st.session_state["edit_mil_id"],),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Milling Record deleted successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        if action_type_mil != "✏️ Edit / 🗑️ Delete Existing Milling":
            st.session_state["edit_mil_id"] = None

    if (
        action_type_mil == "➕ New Milling & Quality Entry"
        or st.session_state["edit_mil_id"] is not None
    ):
        default_miller_m = (
            edit_mil_data["miller_name"] if edit_mil_data is not None else None
        )
        miller_name = get_miller_input("milling_q", default_miller_m)

        edit_q_data = None
        if st.session_state["edit_mil_id"] is not None:
            df_q_all = load_data("quality")
            if not df_q_all.empty and "milling_id" in df_q_all.columns:
                q_match = df_q_all[
                    df_q_all["milling_id"] == st.session_state["edit_mil_id"]
                ]
                if not q_match.empty:
                    edit_q_data = q_match.iloc[0]

        with st.form("milling_quality_form", clear_on_submit=False):
            st.subheader("1. Milling Parameters & Finished Goods Quantity")
            c1, c2 = st.columns(2)
            with c1:
                default_mdate = datetime.date.today()
                if edit_mil_data is not None:
                    try:
                        default_mdate = datetime.datetime.strptime(
                            edit_mil_data["milling_date"], "%d %b %Y"
                        ).date()
                    except Exception:
                        pass
                mil_date_obj = st.date_input("Milling Date", default_mdate)
                milling_date = mil_date_obj.strftime("%d %b %Y")

                default_mqty = (
                    float(edit_mil_data["milling_qty"])
                    if edit_mil_data is not None
                    else 0.0
                )
                milling_qty = st.number_input(
                    "Milling Quantity / Wheat Consumed (kg)",
                    min_value=0.0,
                    value=default_mqty,
                    step=10.0,
                    format="%.2f",
                )

                default_ttime = (
                    edit_mil_data["tempering_time"]
                    if edit_mil_data is not None
                    else ""
                )
                tempering_time = st.text_input(
                    "Tempering Time (Hours)",
                    value=default_ttime,
                    placeholder="e.g. 12 Hours",
                )
            with c2:
                default_twater = (
                    float(edit_mil_data["tempering_water"])
                    if edit_mil_data is not None
                    else 0.0
                )
                tempering_water = st.number_input(
                    "Tempering Water Added (%)",
                    min_value=0.0,
                    value=default_twater,
                    step=0.1,
                    format="%.2f",
                )

                default_fqty = (
                    float(edit_mil_data["finished_qty"])
                    if edit_mil_data is not None and "finished_qty" in edit_mil_data and pd.notnull(edit_mil_data["finished_qty"])
                    else 0.0
                )
                finished_qty = st.number_input(
                    "Finished Output Qty (kg)",
                    min_value=0.0,
                    value=default_fqty,
                    step=10.0,
                    format="%.2f",
                )

            st.divider()
            st.subheader("2. Quality Lab Test Parameters")
            q1, q2, q3, q4 = st.columns(4)
            with q1:
                default_tdate = datetime.date.today()
                if edit_q_data is not None and "test_date" in edit_q_data:
                    try:
                        default_tdate = datetime.datetime.strptime(
                            edit_q_data["test_date"], "%d %b %Y"
                        ).date()
                    except Exception:
                        pass
                test_date_obj = st.date_input("Lab Test Date", default_tdate)
                test_date = test_date_obj.strftime("%d %b %Y")

                default_mois_m = (
                    float(edit_q_data["moisture_milled"])
                    if edit_q_data is not None and pd.notnull(edit_q_data["moisture_milled"])
                    else 0.0
                )
                moisture_milled = st.number_input(
                    "Moisture % (Milled)",
                    min_value=0.0,
                    value=default_mois_m,
                    step=0.1,
                    format="%.1f",
                )
            with q2:
                gran_opts = ["Fine", "Medium", "Coarse"]
                def_gran_idx = 0
                if edit_q_data is not None and "granulation" in edit_q_data and edit_q_data["granulation"] in gran_opts:
                    def_gran_idx = gran_opts.index(edit_q_data["granulation"])
                granulation = st.selectbox("Granulation", gran_opts, index=def_gran_idx)

                default_ccl4 = (
                    edit_q_data["ccl4"]
                    if edit_q_data is not None and "ccl4" in edit_q_data
                    else ""
                )
                ccl4 = st.text_input("CCl4 Test", value=default_ccl4)
            with q3:
                default_ash = (
                    float(edit_q_data["ash_aia"])
                    if edit_q_data is not None and "ash_aia" in edit_q_data and pd.notnull(edit_q_data["ash_aia"])
                    else 0.0
                )
                ash_aia = st.number_input(
                    "Ash / AIA",
                    min_value=0.0,
                    value=default_ash,
                    step=0.01,
                    format="%.2f",
                )

                default_alc = (
                    float(edit_q_data["alcoholic_acidity"])
                    if edit_q_data is not None and "alcoholic_acidity" in edit_q_data and pd.notnull(edit_q_data["alcoholic_acidity"])
                    else 0.0
                )
                alcoholic_acidity = st.number_input(
                    "Alcoholic Acidity",
                    min_value=0.0,
                    value=default_alc,
                    step=0.01,
                    format="%.2f",
                )
            with q4:
                default_wap = (
                    float(edit_q_data["wap"])
                    if edit_q_data is not None and "wap" in edit_q_data and pd.notnull(edit_q_data["wap"])
                    else 0.0
                )
                wap = st.number_input(
                    "WAP",
                    min_value=0.0,
                    value=default_wap,
                    step=0.1,
                    format="%.1f",
                )

                default_gluten = (
                    edit_q_data["gluten"]
                    if edit_q_data is not None and "gluten" in edit_q_data
                    else ""
                )
                gluten = st.text_input("Gluten %", value=default_gluten)

            default_chapati = (
                edit_q_data["chapati_sensory"]
                if edit_q_data is not None and "chapati_sensory" in edit_q_data
                else ""
            )
            chapati_sensory = st.text_input(
                "Chapati Sensory / Quality Remarks",
                value=default_chapati,
            )

            btn_mil_label = (
                "Update Milling & Quality Record"
                if st.session_state["edit_mil_id"] is not None
                else "Save Milling & Quality Entry"
            )
            submit_milling_qual = st.form_submit_button(
                label=btn_mil_label
            )

            if submit_milling_qual:
                conn = get_connection()
                cursor = conn.cursor()

                if st.session_state["edit_mil_id"] is not None:
                    m_id = st.session_state["edit_mil_id"]
                    cursor.execute(
                        """
                        UPDATE milling 
                        SET milling_date=?, miller_name=?, milling_qty=?, tempering_time=?, tempering_water=?, finished_qty=?
                        WHERE id=?
                    """,
                        (
                            milling_date,
                            miller_name,
                            milling_qty,
                            tempering_time,
                            tempering_water,
                            finished_qty,
                            m_id,
                        ),
                    )

                    cursor.execute(
                        "SELECT COUNT(*) FROM quality WHERE milling_id = ?",
                        (m_id,),
                    )
                    if cursor.fetchone()[0] > 0:
                        cursor.execute(
                            """
                            UPDATE quality 
                            SET test_date=?, miller_name=?, moisture_milled=?, granulation=?, ccl4=?, ash_aia=?, alcoholic_acidity=?, wap=?, gluten=?, chapati_sensory=?
                            WHERE milling_id=?
                        """,
                            (
                                test_date,
                                miller_name,
                                moisture_milled,
                                granulation,
                                ccl4,
                                ash_aia,
                                alcoholic_acidity,
                                wap,
                                gluten,
                                chapati_sensory,
                                m_id,
                            ),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                m_id,
                                test_date,
                                miller_name,
                                moisture_milled,
                                granulation,
                                ccl4,
                                ash_aia,
                                alcoholic_acidity,
                                wap,
                                gluten,
                                chapati_sensory,
                            ),
                        )

                    conn.commit()
                    conn.close()
                    st.success("Milling & Quality Record Updated Successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    cursor.execute(
                        """
                        INSERT INTO milling (milling_date, miller_name, milling_qty, tempering_time, tempering_water, finished_qty, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            milling_date,
                            miller_name,
                            milling_qty,
                            tempering_time,
                            tempering_water,
                            finished_qty,
                            current_logged_user,
                        ),
                    )
                    new_milling_id = cursor.lastrowid

                    cursor.execute(
                        """
                        INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            new_milling_id,
                            test_date,
                            miller_name,
                            moisture_milled,
                            granulation,
                            ccl4,
                            ash_aia,
                            alcoholic_acidity,
                            wap,
                            gluten,
                            chapati_sensory,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    email_subject = f"[REPORT] New Milling & Quality Entry - {miller_name}"
                    email_body = f"""
BETTER NUTRITION - MILLING & QUALITY REPORT
===========================================
Neeche nayi Milling aur Lab Quality entry ki poori report di gayi hai:

• Milling Date: {milling_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}
• Milling Qty (Wheat Consumed): {milling_qty:,.2f} kg
• Finished Output Qty: {finished_qty:,.2f} kg
• Tempering Time: {tempering_time}
• Tempering Water Added: {tempering_water}%

QUALITY LAB TEST RESULTS:
• Test Date: {test_date}
• Moisture % (Milled): {moisture_milled}%
• Granulation: {granulation}
• CCl4 Test: {ccl4}
• Ash / AIA: {ash_aia}
• Alcoholic Acidity: {alcoholic_acidity}
• WAP: {wap}
• Gluten %: {gluten}
• Chapati Sensory: {chapati_sensory}

============================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
                    send_email_alert(email_subject, email_body)
                    st.success(
                        "Milling & Quality Data Saved Successfully by"
                        f" {current_logged_user}! Email report sent to Admin."
                    )
                    st.rerun()

    elif action_type_mil == "🛠️ Update Quality for Old Batches":
        st.subheader("Update Quality Parameters for Previous Milling Batches")
        df_pending_mil = load_data("milling")
        if df_pending_mil.empty:
            st.info("Koi milling record available nahi hai.")
        else:
            df_pending_mil["label"] = (
                "ID: "
                + df_pending_mil["id"].astype(str)
                + " | Miller: "
                + df_pending_mil["miller_name"]
                + " | Date: "
                + df_pending_mil["milling_date"]
            )
            selected_old_milling = st.selectbox(
                "Select Milling Batch", df_pending_mil["label"].tolist()
            )
            chosen_mil_row = df_pending_mil[
                df_pending_mil["label"] == selected_old_milling
            ].iloc[0]
            chosen_mil_id = int(chosen_mil_row["id"])

            with st.form("update_old_quality_form"):
                q_date_obj = st.date_input("Lab Test Date", datetime.date.today())
                t_date_str = q_date_obj.strftime("%d %b %Y")

                oq1, oq2, oq3, oq4 = st.columns(4)
                with oq1:
                    u_moisture = st.number_input(
                        "Moisture % (Milled)",
                        min_value=0.0,
                        step=0.1,
                        format="%.1f",
                    )
                with oq2:
                    u_gran = st.selectbox(
                        "Granulation", ["Fine", "Medium", "Coarse"]
                    )
                    u_ccl4 = st.text_input("CCl4 Test")
                with oq3:
                    u_ash = st.number_input(
                        "Ash / AIA", min_value=0.0, step=0.01, format="%.2f"
                    )
                    u_alc = st.number_input(
                        "Alcoholic Acidity",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                    )
                with oq4:
                    u_wap = st.number_input(
                        "WAP", min_value=0.0, step=0.1, format="%.1f"
                    )
                    u_gluten = st.text_input("Gluten %")

                u_chapati = st.text_input(
                    "Chapati Sensory / Quality Remarks"
                )
                submit_old_q = st.form_submit_button(
                    "Save Quality Data for Batch"
                )

                if submit_old_q:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            chosen_mil_id,
                            t_date_str,
                            chosen_mil_row["miller_name"],
                            u_moisture,
                            u_gran,
                            u_ccl4,
                            u_ash,
                            u_alc,
                            u_wap,
                            u_gluten,
                            u_chapati,
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Quality data successfully added for Milling ID {chosen_mil_id}!"
                    )
                    st.rerun()

    st.divider()
    st.subheader("Saved Milling Records")
    df_m_disp = load_data("milling")
    if not df_m_disp.empty:
        st.dataframe(df_m_disp, use_container_width=True)

    st.subheader("Saved Quality Lab Records")
    df_q_disp = load_data("quality")
    if not df_q_disp.empty:
        st.dataframe(df_q_disp, use_container_width=True)

elif menu == "3. Finished Goods & Yield":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Finished Goods Production & Yield Tracking</h1>
            <p>Log flour, bran, and chokar production quantities and monitor manufacturing yield percentages.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "edit_fg_id" not in st.session_state:
        st.session_state["edit_fg_id"] = None

    df_fg_saved = load_data("finished_goods")

    if not df_fg_saved.empty:
        action_type_fg = st.radio(
            "Action Mode",
            ["➕ New Finished Goods Entry", "✏️ Edit / 🗑️ Delete Existing Entry"],
            horizontal=True,
            key="mode_fg",
        )
    else:
        action_type_fg = "➕ New Finished Goods Entry"

    edit_fg_data = None
    if (
        action_type_fg == "✏️ Edit / 🗑️ Delete Existing Entry"
        and not df_fg_saved.empty
    ):
        df_fg_saved["label"] = (
            "ID: "
            + df_fg_saved["id"].astype(str)
            + " | Date: "
            + df_fg_saved["production_date"]
            + " | Miller: "
            + df_fg_saved["miller_name"]
            + " | Total FG: "
            + df_fg_saved["total_finished_qty"].astype(str)
            + " kg"
        )
        selected_fg_label = st.selectbox(
            "Select Finished Goods Record to Modify/Delete",
            df_fg_saved["label"].tolist(),
            key="sel_fg_edit",
        )
        selected_fg_row = df_fg_saved[
            df_fg_saved["label"] == selected_fg_label
        ].iloc[0]
        st.session_state["edit_fg_id"] = int(selected_fg_row["id"])
        edit_fg_data = selected_fg_row

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del_fg = st.checkbox(
                "Haan, main is finished goods record ko permanently delete karna chahta hoon",
                key="conf_del_fg",
            )
            if st.button(
                "🗑️ Confirm & Delete Record",
                type="primary",
                key="btn_del_fg_rec",
            ):
                if confirm_del_fg:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM finished_goods WHERE id = ?",
                        (st.session_state["edit_fg_id"],),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Finished Goods Record ID {st.session_state['edit_fg_id']} successfully deleted!"
                    )
                    st.session_state["edit_fg_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        st.session_state["edit_fg_id"] = None

    if (
        action_type_fg == "➕ New Finished Goods Entry"
        or st.session_state["edit_fg_id"] is not None
    ):
        default_miller_fg = (
            edit_fg_data["miller_name"] if edit_fg_data is not None else None
        )
        miller_name = get_miller_input("fg", default_miller_fg)

        with st.form("finished_goods_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                default_pdate = datetime.date.today()
                if edit_fg_data is not None:
                    try:
                        default_pdate = datetime.datetime.strptime(
                            edit_fg_data["production_date"], "%d %b %Y"
                        ).date()
                    except Exception:
                        pass
                prod_date_obj = st.date_input("Production Date", value=default_pdate)
                production_date = prod_date_obj.strftime("%d %b %Y")

                default_flour = (
                    float(edit_fg_data["flour_qty"])
                    if edit_fg_data is not None
                    else 0.0
                )
                flour_qty = st.number_input(
                    "Flour Quantity (kg)",
                    min_value=0.0,
                    value=default_flour,
                    step=10.0,
                    format="%.2f",
                )

                default_bran = (
                    float(edit_fg_data["bran_qty"])
                    if edit_fg_data is not None
                    else 0.0
                )
                bran_qty = st.number_input(
                    "Bran Quantity (kg)",
                    min_value=0.0,
                    value=default_bran,
                    step=10.0,
                    format="%.2f",
                )
            with c2:
                default_chokar = (
                    float(edit_fg_data["chokar_qty"])
                    if edit_fg_data is not None
                    else 0.0
                )
                chokar_qty = st.number_input(
                    "Chokar Quantity (kg)",
                    min_value=0.0,
                    value=default_chokar,
                    step=10.0,
                    format="%.2f",
                )

                default_fg_rem = (
                    edit_fg_data["remarks"] if edit_fg_data is not None else ""
                )
                remarks = st.text_input("Remarks", value=default_fg_rem)

            btn_fg_label = (
                "Update Finished Goods Record"
                if st.session_state["edit_fg_id"] is not None
                else "Save Finished Goods Entry"
            )
            submit_fg = st.form_submit_button(label=btn_fg_label)

            if submit_fg:
                total_finished_qty = flour_qty + bran_qty + chokar_qty
                conn = get_connection()
                cursor = conn.cursor()

                if st.session_state["edit_fg_id"] is not None:
                    cursor.execute(
                        """
                        UPDATE finished_goods 
                        SET production_date=?, miller_name=?, flour_qty=?, bran_qty=?, chokar_qty=?, total_finished_qty=?, remarks=?
                        WHERE id=?
                    """,
                        (
                            production_date,
                            miller_name,
                            flour_qty,
                            bran_qty,
                            chokar_qty,
                            round(total_finished_qty, 2),
                            remarks,
                            st.session_state["edit_fg_id"],
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Finished Goods Record ID {st.session_state['edit_fg_id']}"
                        " Updated Successfully!"
                    )
                    st.session_state["edit_fg_id"] = None
                    st.rerun()
                else:
                    cursor.execute(
                        """
                        INSERT INTO finished_goods (production_date, miller_name, flour_qty, bran_qty, chokar_qty, total_finished_qty, remarks, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            production_date,
                            miller_name,
                            flour_qty,
                            bran_qty,
                            chokar_qty,
                            round(total_finished_qty, 2),
                            remarks,
                            current_logged_user,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    email_subject = f"[REPORT] New Finished Goods Entry - {miller_name}"
                    email_body = f"""
BETTER NUTRITION - FINISHED GOODS ENTRY REPORT
=============================================
Neeche nayi Finished Goods entry ki poori report di gayi hai:

• Production Date: {production_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}
• Flour Quantity: {flour_qty:,.2f} kg
• Bran Quantity: {bran_qty:,.2f} kg
• Chokar Quantity: {chokar_qty:,.2f} kg
• Total Finished Quantity: {round(total_finished_qty, 2):,.2f} kg
• Remarks: {remarks}

=============================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
                    send_email_alert(email_subject, email_body)
                    st.success(
                        f"Finished Goods Saved Successfully by {current_logged_user}! Total Qty:"
                        f" {total_finished_qty:,.2f} kg. Email report sent to Admin."
                    )
                    st.rerun()

    st.subheader("Saved Finished Goods Entries")
    df_fg_saved_display = load_data("finished_goods")
    if not df_fg_saved_display.empty:
        st.dataframe(df_fg_saved_display, use_container_width=True)

elif menu == "4. Better Nutrition Packing Material":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Better Nutrition Packing Material Inventory</h1>
            <p>Track bag sizes, received quantities, issued bags, and balance stock levels.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "edit_pm_id" not in st.session_state:
        st.session_state["edit_pm_id"] = None

    df_pm_saved = load_data("packing_material")

    if not df_pm_saved.empty:
        action_type_pm = st.radio(
            "Action Mode",
            ["➕ New Packing Material Entry", "✏️ Edit / 🗑️ Delete Existing Entry"],
            horizontal=True,
            key="mode_pm",
        )
    else:
        action_type_pm = "➕ New Packing Material Entry"

    edit_pm_data = None
    if (
        action_type_pm == "✏️ Edit / 🗑️ Delete Existing Entry"
        and not df_pm_saved.empty
    ):
        df_pm_saved["label"] = (
            "ID: "
            + df_pm_saved["id"].astype(str)
            + " | Date: "
            + df_pm_saved["entry_date"]
            + " | Size: "
            + df_pm_saved["bag_size"]
            + " | Bal: "
            + df_pm_saved["balance_bags"].astype(str)
            + " bags"
        )
        selected_pm_label = st.selectbox(
            "Select Packing Material Record to Modify/Delete",
            df_pm_saved["label"].tolist(),
            key="sel_pm_edit",
        )
        selected_pm_row = df_pm_saved[
            df_pm_saved["label"] == selected_pm_label
        ].iloc[0]
        st.session_state["edit_pm_id"] = int(selected_pm_row["id"])
        edit_pm_data = selected_pm_row

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del_pm = st.checkbox(
                "Haan, main is packing material record ko permanently delete karna chahta hoon",
                key="conf_del_pm",
            )
            if st.button(
                "🗑️ Confirm & Delete Record",
                type="primary",
                key="btn_del_pm_rec",
            ):
                if confirm_del_pm:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM packing_material WHERE id = ?",
                        (st.session_state["edit_pm_id"],),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Packing Material Record ID {st.session_state['edit_pm_id']} successfully deleted!"
                    )
                    st.session_state["edit_pm_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        st.session_state["edit_pm_id"] = None

    if (
        action_type_pm == "➕ New Packing Material Entry"
        or st.session_state["edit_pm_id"] is not None
    ):
        default_miller_pm = (
            edit_pm_data["miller_name"] if edit_pm_data is not None else None
        )
        miller_name = get_miller_input("pm", default_miller_pm)

        with st.form("packing_material_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                default_edate = datetime.date.today()
                if edit_pm_data is not None:
                    try:
                        default_edate = datetime.datetime.strptime(
                            edit_pm_data["entry_date"], "%d %b %Y"
                        ).date()
                    except Exception:
                        pass
                entry_date_obj = st.date_input("Entry Date", value=default_edate)
                entry_date = entry_date_obj.strftime("%d %b %Y")

                bag_sizes = ["30 kg Bag", "10 kg Bag", "5 kg Pouch", "Other"]
                default_bs_idx = 0
                if (
                    edit_pm_data is not None
                    and edit_pm_data["bag_size"] in bag_sizes
                ):
                    default_bs_idx = bag_sizes.index(edit_pm_data["bag_size"])
                bag_size = st.selectbox(
                    "Bag Size", bag_sizes, index=default_bs_idx
                )

                default_rec_bags = (
                    int(edit_pm_data["received_bags"])
                    if edit_pm_data is not None
                    else 0
                )
                received_bags = st.number_input(
                    "Received Bags",
                    min_value=0,
                    value=default_rec_bags,
                    step=10,
                )
            with c2:
                default_iss_bags = (
                    int(edit_pm_data["issued_bags"])
                    if edit_pm_data is not None
                    else 0
                )
                issued_bags = st.number_input(
                    "Issued Bags",
                    min_value=0,
                    value=default_iss_bags,
                    step=10,
                )

                default_pm_rem = (
                    edit_pm_data["remarks"] if edit_pm_data is not None else ""
                )
                remarks = st.text_input("Remarks", value=default_pm_rem)

            btn_pm_label = (
                "Update Packing Material Record"
                if st.session_state["edit_pm_id"] is not None
                else "Save Packing Material Entry"
            )
            submit_pm = st.form_submit_button(label=btn_pm_label)

            if submit_pm:
                balance_bags = received_bags - issued_bags
                conn = get_connection()
                cursor = conn.cursor()

                if st.session_state["edit_pm_id"] is not None:
                    cursor.execute(
                        """
                        UPDATE packing_material 
                        SET entry_date=?, miller_name=?, bag_size=?, received_bags=?, issued_bags=?, balance_bags=?, remarks=?
                        WHERE id=?
                    """,
                        (
                            entry_date,
                            miller_name,
                            bag_size,
                            received_bags,
                            issued_bags,
                            balance_bags,
                            remarks,
                            st.session_state["edit_pm_id"],
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Packing Material Record ID {st.session_state['edit_pm_id']}"
                        " Updated Successfully!"
                    )
                    st.session_state["edit_pm_id"] = None
                    st.rerun()
                else:
                    cursor.execute(
                        """
                        INSERT INTO packing_material (entry_date, miller_name, bag_size, received_bags, issued_bags, balance_bags, remarks, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            entry_date,
                            miller_name,
                            bag_size,
                            received_bags,
                            issued_bags,
                            balance_bags,
                            remarks,
                            current_logged_user,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    email_subject = f"[REPORT] New Packing Material Entry - {miller_name}"
                    email_body = f"""
BETTER NUTRITION - PACKING MATERIAL ENTRY REPORT
===============================================
Neeche nayi Packing Material entry ki poori report di gayi hai:

• Entry Date: {entry_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}
• Bag Size: {bag_size}
• Received Bags: {received_bags}
• Issued Bags: {issued_bags}
• Balance Bags: {balance_bags}
• Remarks: {remarks}

===============================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
                    send_email_alert(email_subject, email_body)
                    st.success(
                        f"Packing Material Saved Successfully by {current_logged_user}! Balance Bags:"
                        f" {balance_bags}. Email report sent to Admin."
                    )
                    st.rerun()

    st.subheader("Saved Packing Material Entries")
    df_pm_saved_display = load_data("packing_material")
    if not df_pm_saved_display.empty:
        st.dataframe(df_pm_saved_display, use_container_width=True)

elif menu == "5. Daily Dispatch Entry":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Daily Dispatch Entry</h1>
            <p>Record finished goods dispatches, party names, vehicle numbers, and SKU bag breakdowns.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "edit_disp_id" not in st.session_state:
        st.session_state["edit_disp_id"] = None

    df_disp_saved = load_data("dispatch")

    if not df_disp_saved.empty:
        action_type_disp = st.radio(
            "Action Mode",
            ["➕ New Dispatch Entry", "✏️ Edit / 🗑️ Delete Existing Entry"],
            horizontal=True,
            key="mode_disp",
        )
    else:
        action_type_disp = "➕ New Dispatch Entry"

    edit_disp_data = None
    if (
        action_type_disp == "✏️ Edit / 🗑️ Delete Existing Entry"
        and not df_disp_saved.empty
    ):
        df_disp_saved["label"] = (
            "ID: "
            + df_disp_saved["id"].astype(str)
            + " | Date: "
            + df_disp_saved["dispatch_date"]
            + " | Party: "
            + df_disp_saved["party_name"]
            + " | Total Wt: "
            + df_disp_saved["total_dispatched_wt"].astype(str)
            + " kg"
        )
        selected_disp_label = st.selectbox(
            "Select Dispatch Record to Modify/Delete",
            df_disp_saved["label"].tolist(),
            key="sel_disp_edit",
        )
        selected_disp_row = df_disp_saved[
            df_disp_saved["label"] == selected_disp_label
        ].iloc[0]
        st.session_state["edit_disp_id"] = int(selected_disp_row["id"])
        edit_disp_data = selected_disp_row

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del_disp = st.checkbox(
                "Haan, main is dispatch record ko permanently delete karna chahta hoon",
                key="conf_del_disp",
            )
            if st.button(
                "🗑️ Confirm & Delete Record",
                type="primary",
                key="btn_del_disp_rec",
            ):
                if confirm_del_disp:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM dispatch WHERE id = ?",
                        (st.session_state["edit_disp_id"],),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Dispatch Record ID {st.session_state['edit_disp_id']} successfully deleted!"
                    )
                    st.session_state["edit_disp_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        st.session_state["edit_disp_id"] = None

    if (
        action_type_disp == "➕ New Dispatch Entry"
        or st.session_state["edit_disp_id"] is not None
    ):
        default_miller_disp = (
            edit_disp_data["miller_name"] if edit_disp_data is not None else None
        )
        miller_name = get_miller_input("dispatch", default_miller_disp)

        with st.form("dispatch_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                default_ddate = datetime.date.today()
                if edit_disp_data is not None:
                    try:
                        default_ddate = datetime.datetime.strptime(
                            edit_disp_data["dispatch_date"], "%d %b %Y"
                        ).date()
                    except Exception:
                        pass
                dispatch_date_obj = st.date_input("Dispatch Date", value=default_ddate)
                dispatch_date = dispatch_date_obj.strftime("%d %b %Y")

                default_party = (
                    edit_disp_data["party_name"] if edit_disp_data is not None else ""
                )
                party_name = st.text_input("Party Name", value=default_party)

                default_dveh = (
                    edit_disp_data["vehicle_number"] if edit_disp_data is not None else ""
                )
                vehicle_number = st.text_input(
                    "Vehicle Number",
                    value=default_dveh,
                    placeholder="e.g. UP-75-BT-1234",
                )
            with c2:
                default_b30 = (
                    int(edit_disp_data["bags_30kg"])
                    if edit_disp_data is not None and "bags_30kg" in edit_disp_data and pd.notnull(edit_disp_data["bags_30kg"])
                    else 0
                )
                bags_30kg = st.number_input(
                    "30 kg Bags Count",
                    min_value=0,
                    value=default_b30,
                    step=1,
                )

                default_b10 = (
                    int(edit_disp_data["bags_10kg"])
                    if edit_disp_data is not None and "bags_10kg" in edit_disp_data and pd.notnull(edit_disp_data["bags_10kg"])
                    else 0
                )
                bags_10kg = st.number_input(
                    "10 kg Bags Count",
                    min_value=0,
                    value=default_b10,
                    step=1,
                )
            with c3:
                default_p5 = (
                    int(edit_disp_data["pouches_5kg"])
                    if edit_disp_data is not None and "pouches_5kg" in edit_disp_data and pd.notnull(edit_disp_data["pouches_5kg"])
                    else 0
                )
                pouches_5kg = st.number_input(
                    "5 kg Pouches Count",
                    min_value=0,
                    value=default_p5,
                    step=1,
                )

                default_other = (
                    float(edit_disp_data["other_qty"])
                    if edit_disp_data is not None and "other_qty" in edit_disp_data and pd.notnull(edit_disp_data["other_qty"])
                    else 0.0
                )
                other_qty = st.number_input(
                    "Other Quantity / Weight (kg)",
                    min_value=0.0,
                    value=default_other,
                    step=10.0,
                    format="%.2f",
                )

            default_drem = edit_disp_data["remarks"] if edit_disp_data is not None else ""
            remarks = st.text_input("Remarks", value=default_drem)

            btn_disp_label = (
                "Update Dispatch Record"
                if st.session_state["edit_disp_id"] is not None
                else "Save Dispatch Entry"
            )
            submit_dispatch = st.form_submit_button(label=btn_disp_label)

            if submit_dispatch:
                total_dispatched_wt = (
                    (bags_30kg * 30.0)
                    + (bags_10kg * 10.0)
                    + (pouches_5kg * 5.0)
                    + other_qty
                )
                conn = get_connection()
                cursor = conn.cursor()

                if st.session_state["edit_disp_id"] is not None:
                    cursor.execute(
                        """
                        UPDATE dispatch 
                        SET dispatch_date=?, miller_name=?, party_name=?, vehicle_number=?, bags_30kg=?, bags_10kg=?, pouches_5kg=?, other_qty=?, total_dispatched_wt=?, remarks=?
                        WHERE id=?
                    """,
                        (
                            dispatch_date,
                            miller_name,
                            party_name,
                            vehicle_number,
                            bags_30kg,
                            bags_10kg,
                            pouches_5kg,
                            other_qty,
                            round(total_dispatched_wt, 2),
                            remarks,
                            st.session_state["edit_disp_id"],
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Dispatch Record ID {st.session_state['edit_disp_id']}"
                        " Updated Successfully!"
                    )
                    st.session_state["edit_disp_id"] = None
                    st.rerun()
                else:
                    cursor.execute(
                        """
                        INSERT INTO dispatch (dispatch_date, miller_name, party_name, vehicle_number, bags_30kg, bags_10kg, pouches_5kg, other_qty, total_dispatched_wt, remarks, entered_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            dispatch_date,
                            miller_name,
                            party_name,
                            vehicle_number,
                            bags_30kg,
                            bags_10kg,
                            pouches_5kg,
                            other_qty,
                            round(total_dispatched_wt, 2),
                            remarks,
                            current_logged_user,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    email_subject = f"[REPORT] New Dispatch Entry - {party_name}"
                    email_body = f"""
BETTER NUTRITION - DAILY DISPATCH ENTRY REPORT
==============================================
Neeche nayi Dispatch entry ki poori report di gayi hai:

• Dispatch Date: {dispatch_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}
• Party Name: {party_name}
• Vehicle Number: {vehicle_number}

SKU BREAKDOWN & TOTAL WEIGHT:
• 30 kg Bags: {bags_30kg}
• 10 kg Bags: {bags_10kg}
• 5 kg Pouches: {pouches_5kg}
• Other Qty (kg): {other_qty:,.2f} kg
• Total Dispatched Weight: {round(total_dispatched_wt, 2):,.2f} kg
• Remarks: {remarks}

==============================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
                    send_email_alert(email_subject, email_body)
                    st.success(
                        f"Dispatch Saved Successfully by {current_logged_user}! Total Dispatched:"
                        f" {total_dispatched_wt:,.2f} kg. Email report sent to Admin."
                    )
                    st.rerun()

    st.subheader("Saved Dispatch Entries")
    df_disp_saved_display = load_data("dispatch")
    if not df_disp_saved_display.empty:
        st.dataframe(df_disp_saved_display, use_container_width=True)

elif menu == "6. Master Records & Export (Admin Controls)":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Master Records & Data Export</h1>
            <p>View all database tables, manage user credentials, and download full ERP records.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if user_role != "Admin":
        st.error(
            "Access Denied! Yeh section sirf Admin ke liye restricted hai."
        )
    else:
        st.subheader("Database Tables Viewer")
        selected_table = st.selectbox(
            "Select Table to View",
            [
                "raw_material",
                "milling",
                "quality",
                "finished_goods",
                "packing_material",
                "dispatch",
                "employees",
            ],
        )
        df_master = load_data(selected_table)
        st.dataframe(df_master, use_container_width=True)

        st.divider()
        st.subheader("Employee & User Management")
        df_emp = load_data("employees")
        st.dataframe(df_emp, use_container_width=True)

        with st.form("add_employee_form"):
            st.write("### Add New Team Member")
            new_emp_name = st.text_input("Employee Name")
            new_emp_pin = st.text_input("4-Digit PIN", type="password")
            new_emp_role = st.selectbox("Role", ["Team", "Admin"])
            submit_emp = st.form_submit_button("Add Employee")

            if submit_emp:
                if new_emp_name.strip() and new_emp_pin.strip():
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO employees (employee_name, pin, role) VALUES (?, ?, ?)",
                        (new_emp_name.strip(), new_emp_pin.strip(), new_emp_role),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Employee {new_emp_name.strip()} added successfully!"
                    )
                    st.rerun()
                else:
                    st.error("Please fill in both name and PIN.")
