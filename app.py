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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatch (
            id INTEGER PRIMARY KEY AUTOINCREMENT, dispatch_date TEXT, miller_name TEXT, party_name TEXT, vehicle_number TEXT, item_name TEXT, bags_dispatched INTEGER, total_dispatched_wt REAL, remarks TEXT, entered_by TEXT
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
                    else None
                )
                milling_qty = st.number_input(
                    "Milling Quantity (Input RM kg)",
                    value=default_mqty,
                    placeholder="Type qty...",
                    step=10.0,
                )

                default_fqty = (
                    float(edit_mil_data["finished_qty"])
                    if (
                        edit_mil_data is not None
                        and "finished_qty" in edit_mil_data
                        and pd.notna(edit_mil_data["finished_qty"])
                    )
                    else None
                )
                finished_qty = st.number_input(
                    "Finished Goods Quantity Produced (kg)",
                    value=default_fqty,
                    placeholder="Type finished goods qty...",
                    step=10.0,
                )
            with c2:
                default_ttime = (
                    edit_mil_data["tempering_time"]
                    if edit_mil_data is not None
                    else ""
                )
                tempering_time = st.text_input(
                    "Tempering Time", value=default_ttime
                )

                default_twater = (
                    float(edit_mil_data["tempering_water"])
                    if edit_mil_data is not None
                    else None
                )
                tempering_water = st.number_input(
                    "Tempering Water (Ltr)",
                    value=default_twater,
                    placeholder="Type water...",
                    step=10.0,
                )

            st.divider()
            st.subheader("2. Quality Lab Parameters")
            qc1, qc2, qc3 = st.columns(3)
            with qc1:
                default_qdate = datetime.date.today()
                if edit_q_data is not None:
                    try:
                        default_qdate = datetime.datetime.strptime(
                            edit_q_data["test_date"], "%d %b %Y"
                        ).date()
                    except Exception:
                        pass
                q_date_obj = st.date_input("Lab Test Date", default_qdate)
                q_date = q_date_obj.strftime("%d %b %Y")

                default_mois_m = (
                    float(edit_q_data["moisture_milled"])
                    if edit_q_data is not None
                    else None
                )
                moisture_milled = st.number_input(
                    "Moisture % (Milled)",
                    value=default_mois_m,
                    placeholder="Type moisture...",
                    step=0.1,
                )

                default_gran = (
                    edit_q_data["granulation"]
                    if edit_q_data is not None
                    else ""
                )
                granulation = st.text_input("Granulation", value=default_gran)
            with qc2:
                default_ccl4 = (
                    edit_q_data["ccl4"] if edit_q_data is not None else ""
                )
                ccl4 = st.text_input("CCL4", value=default_ccl4)

                default_ash = (
                    float(edit_q_data["ash_aia"])
                    if edit_q_data is not None
                    else None
                )
                ash_aia = st.number_input(
                    "Ash + AIA",
                    value=default_ash,
                    placeholder="Type ash...",
                    step=0.01,
                    format="%.3f",
                )

                default_acid = (
                    float(edit_q_data["alcoholic_acidity"])
                    if edit_q_data is not None
                    else None
                )
                alcoholic_acidity = st.number_input(
                    "Alcoholic Acidity",
                    value=default_acid,
                    placeholder="Type acidity...",
                    step=0.001,
                    format="%.4f",
                )
            with qc3:
                default_wap = (
                    float(edit_q_data["wap"])
                    if edit_q_data is not None
                    else None
                )
                wap = st.number_input(
                    "WAP",
                    value=default_wap,
                    placeholder="Type WAP...",
                    step=0.01,
                    format="%.2f",
                )

                default_gluten = (
                    edit_q_data["gluten"] if edit_q_data is not None else ""
                )
                gluten = st.text_input("Gluten", value=default_gluten)

                sensory_opts = ["Excellent", "Good", "Average", "Poor"]
                default_sens_idx = 0
                if (
                    edit_q_data is not None
                    and edit_q_data["chapati_sensory"] in sensory_opts
                ):
                    default_sens_idx = sensory_opts.index(
                        edit_q_data["chapati_sensory"]
                    )
                chapati_sensory = st.selectbox(
                    "Chapati Sensory", sensory_opts, index=default_sens_idx
                )

            btn_label_mil = (
                "Update Milling & Quality Data"
                if st.session_state["edit_mil_id"] is not None
                else "Save Milling & Quality Data"
            )
            submit_both = st.form_submit_button(label=btn_label_mil)

            if submit_both:
                final_mil_qty = (
                    milling_qty if milling_qty is not None else 0.0
                )
                final_fin_qty = (
                    finished_qty if finished_qty is not None else 0.0
                )
                final_temp_water = (
                    tempering_water if tempering_water is not None else 0.0
                )
                final_mois_milled = (
                    moisture_milled if moisture_milled is not None else 0.0
                )
                final_ash = ash_aia if ash_aia is not None else 0.0
                final_acidity = (
                    alcoholic_acidity if alcoholic_acidity is not None else 0.0
                )
                final_wap = wap if wap is not None else 0.0

                conn = get_connection()
                cursor = conn.cursor()

                if st.session_state["edit_mil_id"] is not None:
                    cursor.execute(
                        """
                        UPDATE milling 
                        SET milling_date=?, miller_name=?, milling_qty=?, tempering_time=?, tempering_water=?, finished_qty=?
                        WHERE id=?
                    """,
                        (
                            milling_date,
                            miller_name,
                            final_mil_qty,
                            tempering_time,
                            final_temp_water,
                            final_fin_qty,
                            st.session_state["edit_mil_id"],
                        ),
                    )
                    if edit_q_data is not None:
                        cursor.execute(
                            """
                            UPDATE quality 
                            SET test_date=?, miller_name=?, moisture_milled=?, granulation=?, ccl4=?, ash_aia=?, alcoholic_acidity=?, wap=?, gluten=?, chapati_sensory=?
                            WHERE milling_id=?
                        """,
                            (
                                q_date,
                                miller_name,
                                final_mois_milled,
                                granulation,
                                ccl4,
                                final_ash,
                                final_acidity,
                                final_wap,
                                gluten,
                                chapati_sensory,
                                st.session_state["edit_mil_id"],
                            ),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                st.session_state["edit_mil_id"],
                                q_date,
                                miller_name,
                                final_mois_milled,
                                granulation,
                                ccl4,
                                final_ash,
                                final_acidity,
                                final_wap,
                                gluten,
                                chapati_sensory,
                            ),
                        )
                    conn.commit()
                    conn.close()
                    st.success(
                        f"Milling & Quality Data Updated Successfully for Batch ID"
                        f" {st.session_state['edit_mil_id']}!"
                    )
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
                            final_mil_qty,
                            tempering_time,
                            final_temp_water,
                            final_fin_qty,
                            current_logged_user,
                        ),
                    )
                    milling_id = cursor.lastrowid
                    cursor.execute(
                        """
                        INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            milling_id,
                            q_date,
                            miller_name,
                            final_mois_milled,
                            granulation,
                            ccl4,
                            final_ash,
                            final_acidity,
                            final_wap,
                            gluten,
                            chapati_sensory,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    email_subject = f"[REPORT] Milling & Finished Goods Entry - {miller_name}"
                    email_body = f"""
BETTER NUTRITION - MILLING, FINISHED GOODS & QUALITY LAB REPORT
=============================================================
Neeche nayi Milling aur Quality entry ki poori report di gayi hai:

• Milling Date: {milling_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}

PRODUCTION PARAMETERS:
• Input Milling Quantity: {final_mil_qty:,.2f} kg
• Finished Goods Quantity (Produced): {final_fin_qty:,.2f} kg
• Tempering Time: {tempering_time}
• Tempering Water: {final_temp_water:,.2f} Ltr

QUALITY LAB TEST PARAMETERS (Test Date: {q_date}):
• Moisture % (Milled): {final_mois_milled}%
• Granulation: {granulation}
• CCL4 Test: {ccl4}
• Ash + AIA: {final_ash}
• Alcoholic Acidity: {final_acidity}
• WAP: {final_wap}
• Gluten: {gluten}
• Chapati Sensory: {chapati_sensory}

=============================================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
                    send_email_alert(email_subject, email_body)
                    st.success(
                        f"Milling, Finished Goods & Quality Data Successfully"
                        f" Saved by {current_logged_user}! Email report sent to"
                        " Admin."
                    )
                    st.rerun()

    elif action_type_mil == "🛠️ Update Quality for Old Batches":
        st.subheader("Purane Milling Batches Jinme Quality Data Missing Hai")
        df_mil_all = load_data("milling")
        df_q_all = load_data("quality")

        if df_mil_all.empty:
            st.info("Phele kuch milling entries karein.")
        else:
            existing_q_mids = (
                df_q_all["milling_id"].tolist()
                if (not df_q_all.empty and "milling_id" in df_q_all.columns)
                else []
            )
            df_pending_q = df_mil_all[
                ~df_mil_all["id"].isin(existing_q_mids)
            ].copy()

            if df_pending_q.empty:
                st.success(
                    "Sabhi milling batches ke liye quality data already entered"
                    " hai!"
                )
            else:
                df_pending_q["label"] = (
                    "Batch ID: "
                    + df_pending_q["id"].astype(str)
                    + " | Miller: "
                    + df_pending_q["miller_name"]
                    + " | Date: "
                    + df_pending_q["milling_date"]
                    + " | Qty: "
                    + df_pending_q["milling_qty"].astype(str)
                    + " kg"
                )
                sel_pending = st.selectbox(
                    "Select Pending Milling Batch for Quality Entry",
                    df_pending_q["label"].tolist(),
                    key="sel_pend_q",
                )
                selected_pend_row = df_pending_q[
                    df_pending_q["label"] == sel_pending
                ].iloc[0]
                target_mil_id = int(selected_pend_row["id"])
                target_miller = selected_pend_row["miller_name"]

                with st.form("pending_quality_form"):
                    st.write(
                        f"**Adding Quality Data for Batch ID: {target_mil_id}"
                        f" ({target_miller})**"
                    )
                    qc1, qc2, qc3 = st.columns(3)
                    with qc1:
                        q_date_obj = st.date_input(
                            "Lab Test Date", datetime.date.today(), key="pq_date"
                        )
                        q_date = q_date_obj.strftime("%d %b %Y")
                        moisture_milled = st.number_input(
                            "Moisture % (Milled)",
                            min_value=0.0,
                            value=12.0,
                            step=0.1,
                            format="%.1f",
                            key="pq_mois",
                        )
                        granulation = st.text_input(
                            "Granulation", key="pq_gran"
                        )
                    with qc2:
                        ccl4 = st.text_input("CCL4", key="pq_ccl4")
                        ash_aia = st.number_input(
                            "Ash + AIA",
                            min_value=0.0,
                            value=0.5,
                            step=0.01,
                            format="%.3f",
                            key="pq_ash",
                        )
                        alcoholic_acidity = st.number_input(
                            "Alcoholic Acidity",
                            min_value=0.0,
                            value=0.05,
                            step=0.001,
                            format="%.4f",
                            key="pq_acid",
                        )
                    with qc3:
                        wap = st.number_input(
                            "WAP",
                            min_value=0.0,
                            value=60.0,
                            step=0.01,
                            format="%.2f",
                            key="pq_wap",
                        )
                        gluten = st.text_input("Gluten", key="pq_glut")
                        sensory_opts = ["Excellent", "Good", "Average", "Poor"]
                        chapati_sensory = st.selectbox(
                            "Chapati Sensory", sensory_opts, key="pq_sens"
                        )

                    submit_pend_q = st.form_submit_button(
                        "Save Quality Data for Old Batch"
                    )
                    if submit_pend_q:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                target_mil_id,
                                q_date,
                                target_miller,
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
                        st.success(
                            f"Quality Data Successfully Added for Batch ID"
                            f" {target_mil_id}!"
                        )
                        st.rerun()

    st.subheader("Saved Milling & Quality Records")
    df_m_saved = load_data("milling")
    df_q_saved = load_data("quality")
    if not df_m_saved.empty:
        if not df_q_saved.empty and "milling_id" in df_q_saved.columns:
            df_combined = pd.merge(
                df_m_saved,
                df_q_saved,
                left_on="id",
                right_on="milling_id",
                how="left",
                suffixes=("_milling", "_quality"),
            )
            st.dataframe(df_combined, use_container_width=True)
        else:
            st.dataframe(df_m_saved, use_container_width=True)

elif menu == "3. Finished Goods & Yield":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Finished Goods Production & Yield Tracking</h1>
            <p>Log production quantities of Flour, Bran, and Chokar with automatic yield calculation.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    miller_name = get_miller_input("fg_section")

    with st.form("finished_goods_form"):
        c1, c2 = st.columns(2)
        with c1:
            prod_date_obj = st.date_input(
                "Production Date", datetime.date.today()
            )
            production_date = prod_date_obj.strftime("%d %b %Y")

            flour_qty = st.number_input(
                "Flour Production Qty (kg)", min_value=0.0, step=10.0
            )
            bran_qty = st.number_input(
                "Bran Production Qty (kg)", min_value=0.0, step=10.0
            )
        with c2:
            chokar_qty = st.number_input(
                "Chokar Production Qty (kg)", min_value=0.0, step=10.0
            )
            remarks = st.text_input("Production Remarks")

        total_finished = flour_qty + bran_qty + chokar_qty
        st.info(f"**Total Finished Goods Calculated:** {total_finished:,.2f} kg")

        submit_fg = st.form_submit_button("Save Finished Goods Entry")

        if submit_fg:
            conn = get_connection()
            cursor = conn.cursor()
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
                    total_finished,
                    remarks,
                    current_logged_user,
                ),
            )
            conn.commit()
            conn.close()

            email_subject = f"[REPORT] Finished Goods Entry - {miller_name}"
            email_body = f"""
BETTER NUTRITION - FINISHED GOODS PRODUCTION REPORT
==================================================
Neeche nayi Finished Goods entry ki poori report di gayi hai:

• Production Date: {production_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}

PRODUCTION BREAKDOWN:
• Flour Qty: {flour_qty:,.2f} kg
• Bran Qty: {bran_qty:,.2f} kg
• Chokar Qty: {chokar_qty:,.2f} kg
• Total Finished Goods Qty: {total_finished:,.2f} kg
• Remarks: {remarks}

==================================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
            send_email_alert(email_subject, email_body)
            st.success(
                f"Finished Goods Successfully Saved by {current_logged_user}!"
                " Email report sent to Admin."
            )
            st.rerun()

    st.subheader("Saved Finished Goods Entries")
    df_fg_saved = load_data("finished_goods")
    if not df_fg_saved.empty:
        st.dataframe(df_fg_saved, use_container_width=True)

elif menu == "4. Better Nutrition Packing Material":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Better Nutrition Packing Material Management</h1>
            <p>Track bag sizes, received bags, issued bags, and current stock balance.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    miller_name = get_miller_input("pm_section")

    with st.form("packing_material_form"):
        c1, c2 = st.columns(2)
        with c1:
            entry_date_obj = st.date_input("Entry Date", datetime.date.today())
            entry_date = entry_date_obj.strftime("%d %b %Y")

            bag_size = st.selectbox(
                "Bag Size / Type",
                ["30 kg Bag", "50 kg Bag", "10 kg Bag", "5 kg Bag", "Other"],
            )
            received_bags = st.number_input(
                "Received Bags", min_value=0, step=1
            )
        with c2:
            issued_bags = st.number_input("Issued Bags", min_value=0, step=1)
            remarks = st.text_input("Packing Material Remarks")

        balance_bags = received_bags - issued_bags
        st.info(
            f"**Net Balance Bags Calculated:** {balance_bags:,} bags ({bag_size})"
        )

        submit_pm = st.form_submit_button("Save Packing Material Entry")

        if submit_pm:
            conn = get_connection()
            cursor = conn.cursor()
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

            email_subject = (
                f"[REPORT] Packing Material Entry - {bag_size} ({miller_name})"
            )
            email_body = f"""
BETTER NUTRITION - PACKING MATERIAL STOCK REPORT
===============================================
Neeche nayi Packing Material entry ki poori report di gayi hai:

• Entry Date: {entry_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}

PACKING STOCK DETAILS:
• Bag Size/Type: {bag_size}
• Received Bags: {received_bags:,}
• Issued Bags: {issued_bags:,}
• Balance Bags: {balance_bags:,}
• Remarks: {remarks}

===============================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
            send_email_alert(email_subject, email_body)
            st.success(
                f"Packing Material Successfully Saved by {current_logged_user}!"
                " Email report sent to Admin."
            )
            st.rerun()

    st.subheader("Saved Packing Material Entries")
    df_pm_saved = load_data("packing_material")
    if not df_pm_saved.empty:
        st.dataframe(df_pm_saved, use_container_width=True)

elif menu == "5. Daily Dispatch Entry":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Daily Dispatch Entry & Management</h1>
            <p>Log outgoing stock dispatches, party names, vehicles, and total dispatched weights.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    miller_name = get_miller_input("disp_section")

    with st.form("dispatch_form"):
        c1, c2 = st.columns(2)
        with c1:
            disp_date_obj = st.date_input(
                "Dispatch Date", datetime.date.today()
            )
            dispatch_date = disp_date_obj.strftime("%d %b %Y")

            party_name = st.text_input("Party Name / Customer Name")
            vehicle_no = st.text_input("Vehicle Number", placeholder="e.g. UP-75-XYZ-1234")
        with c2:
            item_name = st.selectbox(
                "Item Dispatched", ["Flour", "Bran", "Chokar", "Mixed / Other"]
            )
            bags_dispatched = st.number_input(
                "Bags Dispatched", min_value=0, step=1
            )
            total_dispatched_wt = st.number_input(
                "Total Dispatched Weight (kg)", min_value=0.0, step=10.0
            )

        remarks = st.text_input("Dispatch Remarks")
        submit_disp = st.form_submit_button("Save Dispatch Entry")

        if submit_disp:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dispatch (dispatch_date, miller_name, party_name, vehicle_number, item_name, bags_dispatched, total_dispatched_wt, remarks, entered_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    dispatch_date,
                    miller_name,
                    party_name,
                    vehicle_no,
                    item_name,
                    bags_dispatched,
                    total_dispatched_wt,
                    remarks,
                    current_logged_user,
                ),
            )
            conn.commit()
            conn.close()

            email_subject = (
                f"[REPORT] Daily Dispatch Entry - Party: {party_name}"
            )
            email_body = f"""
BETTER NUTRITION - DAILY STOCK DISPATCH REPORT
==============================================
Neeche nayi Dispatch entry ki poori report di gayi hai:

• Dispatch Date: {dispatch_date}
• Entered By (User): {current_logged_user}
• Miller Name: {miller_name}
• Party / Customer Name: {party_name}
• Vehicle Number: {vehicle_no}

DISPATCH DETAILS:
• Item Dispatched: {item_name}
• Bags Dispatched: {bags_dispatched:,}
• Total Dispatched Weight: {total_dispatched_wt:,.2f} kg
• Remarks: {remarks}

==============================================
Yeh email Better Nutrition ERP System se automatically bheji gayi hai.
"""
            send_email_alert(email_subject, email_body)
            st.success(
                f"Dispatch Entry Successfully Saved by {current_logged_user}!"
                " Email report sent to Admin."
            )
            st.rerun()

    st.subheader("Saved Dispatch Entries")
    df_disp_saved = load_data("dispatch")
    if not df_disp_saved.empty:
        st.dataframe(df_disp_saved, use_container_width=True)

elif menu == "6. Master Records & Export (Admin Controls)":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>Admin Controls & Master Records Export</h1>
            <p>Manage employees, view all system master data tables, and export reports.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if current_logged_user != "Rishabh Admin":
        st.warning(
            "Yeh section sirf Admin (Rishabh Admin) ke liye accessible hai."
        )
    else:
        st.write("### 👥 Employees & PIN Master")
        df_emp = load_data("employees")
        st.dataframe(df_emp, use_container_width=True)

        st.divider()
        st.write("### 📦 All System Master Records & Export Data")

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "Raw Material",
                "Milling & Quality",
                "Finished Goods",
                "Packing Material",
                "Dispatch",
            ]
        )

        with tab1:
            df_rm_all = load_data("raw_material")
            if df_rm_all.empty:
                st.info("No Raw Material records available.")
            else:
                st.dataframe(df_rm_all, use_container_width=True)
                csv_rm = df_rm_all.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Raw Material CSV",
                    csv_rm,
                    "raw_material_master.csv",
                    "text/csv",
                )

        with tab2:
            df_m_all = load_data("milling")
            df_q_all = load_data("quality")
            if df_m_all.empty:
                st.info("No Milling records available.")
            else:
                if not df_q_all.empty and "milling_id" in df_q_all.columns:
                    df_mq_comb = pd.merge(
                        df_m_all,
                        df_q_all,
                        left_on="id",
                        right_on="milling_id",
                        how="left",
                        suffixes=("_milling", "_quality"),
                    )
                else:
                    df_mq_comb = df_m_all
                st.dataframe(df_mq_comb, use_container_width=True)
                csv_mq = df_mq_comb.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Milling & Quality CSV",
                    csv_mq,
                    "milling_quality_master.csv",
                    "text/csv",
                )

        with tab3:
            df_fg_all = load_data("finished_goods")
            if df_fg_all.empty:
                st.info("No Finished Goods records available.")
            else:
                st.dataframe(df_fg_all, use_container_width=True)
                csv_fg = df_fg_all.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Finished Goods CSV",
                    csv_fg,
                    "finished_goods_master.csv",
                    "text/csv",
                )

        with tab4:
            df_pm_all = load_data("packing_material")
            if df_pm_all.empty:
                st.info("No Packing Material records available.")
            else:
                st.dataframe(df_pm_all, use_container_width=True)
                csv_pm = df_pm_all.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Packing Material CSV",
                    csv_pm,
                    "packing_material_master.csv",
                    "text/csv",
                )

        with tab5:
            df_disp_all = load_data("dispatch")
            if df_disp_all.empty:
                st.info("No Dispatch records available.")
            else:
                st.dataframe(df_disp_all, use_container_width=True)
                csv_disp = df_disp_all.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Dispatch CSV",
                    csv_disp,
                    "dispatch_master.csv",
                    "text/csv",
                )
