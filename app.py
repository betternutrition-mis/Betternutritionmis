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
            id INTEGER PRIMARY KEY AUTOINCREMENT, production_date TEXT, miller_name TEXT, sku TEXT, mrp REAL, qty_in_pouches INTEGER, batch_code TEXT, mfd_date TEXT, use_by_date TEXT, bran_qty REAL, chokar_qty REAL, total_finished_qty REAL, remarks TEXT, entered_by TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packing_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT, entry_date TEXT, miller_name TEXT, bag_size TEXT, received_bags INTEGER, issued_bags INTEGER, balance_bags INTEGER, remarks TEXT, entered_by TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatch (
            id INTEGER PRIMARY KEY AUTOINCREMENT, dispatch_date TEXT, miller_name TEXT, party_name TEXT, vehicle_number TEXT, pouches_500g INTEGER, bags_1kg INTEGER, bags_2kg INTEGER, pouches_5kg INTEGER, other_qty REAL, total_dispatched_wt REAL, remarks TEXT, entered_by TEXT
        )
    """)

    for col_query in [
        "ALTER TABLE quality ADD COLUMN wap REAL",
        "ALTER TABLE raw_material ADD COLUMN entered_by TEXT",
        "ALTER TABLE milling ADD COLUMN entered_by TEXT",
        "ALTER TABLE milling ADD COLUMN finished_qty REAL",
        "ALTER TABLE finished_goods ADD COLUMN entered_by TEXT",
        "ALTER TABLE finished_goods ADD COLUMN sku TEXT",
        "ALTER TABLE finished_goods ADD COLUMN mrp REAL",
        "ALTER TABLE finished_goods ADD COLUMN qty_in_pouches INTEGER",
        "ALTER TABLE finished_goods ADD COLUMN batch_code TEXT",
        "ALTER TABLE finished_goods ADD COLUMN mfd_date TEXT",
        "ALTER TABLE finished_goods ADD COLUMN use_by_date TEXT",
        "ALTER TABLE packing_material ADD COLUMN entered_by TEXT",
        "ALTER TABLE dispatch ADD COLUMN entered_by TEXT",
        "ALTER TABLE dispatch ADD COLUMN pouches_500g INTEGER",
        "ALTER TABLE dispatch ADD COLUMN bags_1kg INTEGER",
        "ALTER TABLE dispatch ADD COLUMN bags_2kg INTEGER",
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

elif menu == "3. Finished Goods & Yield":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Finished Goods & Yield Entry</h1>
            <p>Log production data SKU-wise (500gm, 1kg, 2kg, 5kg) along with Batch Codes, MRP, Pouches, and Bran.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    miller_name_fg = get_miller_input("fg_miller")

    with st.form("finished_goods_form"):
        c1, c2 = st.columns(2)
        with c1:
            prod_date = st.date_input("Production Date", value=datetime.date.today())
        with c2:
            mfd_date = st.date_input("MFD Date", value=datetime.date.today())
            use_by_date = st.date_input("Use By Date", value=datetime.date.today() + datetime.timedelta(days=90))

        st.subheader("SKU 500GM")
        col_500_1, col_500_2, col_500_3 = st.columns(3)
        with col_500_1:
            batch_500 = st.text_input("Batch Code (500GM)")
        with col_500_2:
            mrp_500 = st.number_input("MRP (500GM)", min_value=0.0, step=1.0)
        with col_500_3:
            pouches_500 = st.number_input("Number of Pouch (500GM)", min_value=0, step=1)
        calc_500_kg = (pouches_500 * 0.5)
        st.info(f"Auto Calculate in KG (500GM): **{calc_500_kg:,.2f} kg**")

        st.divider()

        st.subheader("SKU 1KG")
        col_1k_1, col_1k_2, col_1k_3 = st.columns(3)
        with col_1k_1:
            batch_1k = st.text_input("Batch Code (1KG)")
        with col_1k_2:
            mrp_1k = st.number_input("MRP (1KG)", min_value=0.0, step=1.0)
        with col_1k_3:
            pouches_1k = st.number_input("Number of Pouch (1KG)", min_value=0, step=1)
        calc_1k_kg = (pouches_1k * 1.0)
        st.info(f"Auto Calculate in KG (1KG): **{calc_1k_kg:,.2f} kg**")

        st.divider()

        st.subheader("SKU 2KG")
        col_2k_1, col_2k_2, col_2k_3 = st.columns(3)
        with col_2k_1:
            batch_2k = st.text_input("Batch Code (2KG)")
        with col_2k_2:
            mrp_2k = st.number_input("MRP (2KG)", min_value=0.0, step=1.0)
        with col_2k_3:
            pouches_2k = st.number_input("Number of Pouch (2KG)", min_value=0, step=1)
        calc_2k_kg = (pouches_2k * 2.0)
        st.info(f"Auto Calculate in KG (2KG): **{calc_2k_kg:,.2f} kg**")

        st.divider()

        st.subheader("SKU 5KG")
        col_5k_1, col_5k_2, col_5k_3 = st.columns(3)
        with col_5k_1:
            batch_5k = st.text_input("Batch Code (5KG)")
        with col_5k_2:
            mrp_5k = st.number_input("MRP (5KG)", min_value=0.0, step=1.0)
        with col_5k_3:
            pouches_5k = st.number_input("Number of Pouch (5KG)", min_value=0, step=1)
        calc_5k_kg = (pouches_5k * 5.0)
        st.info(f"Auto Calculate in KG (5KG): **{calc_5k_kg:,.2f} kg**")

        st.divider()

        st.subheader("Bran in KG")
        bran_in_kg = st.number_input("Bran (in KG)", min_value=0.0, step=0.1)

        remarks_fg = st.text_input("Remarks / Notes")
        submit_fg = st.form_submit_button("Save Finished Goods Entry")

        if submit_fg:
            total_fg_wt = calc_500_kg + calc_1k_kg + calc_2k_kg + calc_5k_kg + bran_in_kg
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO finished_goods (production_date, miller_name, sku, mrp, qty_in_pouches, batch_code, mfd_date, use_by_date, bran_qty, total_finished_qty, remarks, entered_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    prod_date.strftime("%d %b %Y"),
                    miller_name_fg,
                    "Multi-SKU",
                    0.0,
                    pouches_500 + pouches_1k + pouches_2k + pouches_5k,
                    f"500G:{batch_500}|1KG:{batch_1k}|2KG:{batch_2k}|5KG:{batch_5k}",
                    mfd_date.strftime("%d %b %Y"),
                    use_by_date.strftime("%d %b %Y"),
                    bran_in_kg,
                    total_fg_wt,
                    remarks_fg,
                    current_logged_user,
                ),
            )
            conn.commit()
            conn.close()
            st.success(f"Finished Goods entry successfully saved! Total Finished Weight: {total_fg_wt:,.2f} kg")

    st.subheader("Saved Finished Goods Entries")
    df_fg_saved = load_data("finished_goods")
    if not df_fg_saved.empty:
        st.dataframe(df_fg_saved, use_container_width=True)

elif menu == "4. Better Nutrition Packing Material":
    st.markdown("### Packing Material Management")
    df_pm = load_data("packing_material")
    if not df_pm.empty:
        st.dataframe(df_pm, use_container_width=True)
    else:
        st.info("No packing material records found.")

elif menu == "5. Daily Dispatch Entry":
    st.markdown("### Daily Dispatch Management")
    df_disp = load_data("dispatch")
    if not df_disp.empty:
        st.dataframe(df_disp, use_container_width=True)
    else:
        st.info("No dispatch records found.")

elif menu == "6. Master Records & Export (Admin Controls)":
    st.markdown("### Master Records & Admin Controls")
    if user_role != "Admin":
        st.error("Access Denied! Only Admin can access this section.")
    else:
        st.success("Welcome to Admin Master Controls.")
        df_emp = load_data("employees")
        st.subheader("Employee List")
        st.dataframe(df_emp, use_container_width=True)
