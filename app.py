import datetime
import sqlite3
import pandas as pd
import streamlit as st

# Page Configuration & Theme Header
st.set_page_config(
    page_title="Better Nutrition & Flour Mill ERP", page_icon="🌾", layout="wide"
)

# --- CUSTOM BRANDING HEADER ---
st.markdown(
    "<h1 style='text-align: center; color: #2E7D32;'>🏢 BETTER NUTRITION & FLOUR"
    " MILL ERP</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #555; font-size: 16px;'>Permanent"
    " Modular Enterprise MIS with SQLite Storage</p>",
    unsafe_allow_html=True,
)
st.divider()


# --- ROLE-BASED PASSWORD PROTECTION SYSTEM ---
def check_password():
    """Returns True if the user enters a valid password and sets their role."""

    def password_entered():
        entered_pwd = st.session_state["password"]
        if entered_pwd == "Rishabh@1994":  # Admin Password
            st.session_state["password_correct"] = True
            st.session_state["role"] = "Admin"
            del st.session_state["password"]
        elif entered_pwd == "team123":  # Team Password
            st.session_state["password_correct"] = True
            st.session_state["role"] = "Team"
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "🔒 Password daliye app kholne ke liye:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "🔒 Password daliye app kholne ke liye:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("😕 Password galat hai. Dobara koshish karein.")
        return False
    else:
        return True


if not check_password():
    st.stop()

user_role = st.session_state.get("role", "Team")
st.sidebar.write(f"👤 Logged in as: **{user_role}**")

# Predefined Miller List with 'Other' Option
BASE_MILLER_LIST = [
    "Shree Balram Agro",
    "IKON ORG.",
    "Sathvik Agro",
    "Satya Naraian Kesho",
    "Tara Grains",
    "Other",
]


# --- SQLITE DATABASE CONNECTION & SETUP ---
def get_connection():
    conn = sqlite3.connect("flour_mill_erp.db", check_same_thread=False)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rm_date TEXT,
            miller_name TEXT,
            vendor_name TEXT,
            vehicle_number TEXT,
            hectoliter_weight REAL,
            moisture_rm REAL,
            broken_pct REAL,
            infestation TEXT,
            jute_bags INTEGER,
            gross_qty REAL,
            jute_weight REAL,
            net_weight REAL,
            remarks TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milling (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milling_date TEXT,
            miller_name TEXT,
            milling_qty REAL,
            tempering_time TEXT,
            tempering_water REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            miller_name TEXT,
            moisture_milled REAL,
            granulation TEXT,
            ccl4 TEXT,
            ash_aia REAL,
            alcoholic_acidity REAL,
            gluten TEXT,
            chapati_sensory TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finished_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            production_date TEXT,
            miller_name TEXT,
            mfd_date TEXT,
            expiry_date TEXT,
            mrp REAL,
            product_code TEXT,
            pouch_500g INTEGER,
            pouch_1kg INTEGER,
            pouch_2kg INTEGER,
            pouch_5kg INTEGER,
            total_finished_qty REAL,
            bran_qty REAL,
            bran_pct TEXT,
            refraction_qty REAL,
            refraction_pct TEXT,
            yield_pct TEXT,
            processing_loss_pct TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packing_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            miller_name TEXT,
            carton_type TEXT,
            cartons_sent INTEGER,
            tape_sent INTEGER,
            oxysorb_qty INTEGER,
            roll_sku TEXT,
            roll_qty_sent INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatch (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispatch_date TEXT,
            miller_name TEXT,
            vehicle_no TEXT,
            disp_500g INTEGER,
            disp_1kg INTEGER,
            disp_2kg INTEGER,
            disp_5kg INTEGER,
            total_dispatched_wt REAL,
            cartons_used INTEGER,
            remarks TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


def load_data(table_name):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


# --- SIDEBAR NAVIGATION ---
menu = st.sidebar.selectbox(
    "Navigation Menu",
    [
        "📊 Month-wise Summary Dashboard",
        "📥 1. Raw Material Received",
        "⚙️ 2. Milling & Processing",
        "🧪 3. Quality Lab Parameters",
        "📦 4. Finished Goods & Yield",
        "🏷️ 5. Better Nutrition Packing Material",
        "🚚 6. Daily Dispatch Entry",
        "📂 7. Master Records & Export (Admin Controls)",
    ],
)


def get_miller_input(unique_key):
    st.write("### Select Miller Details")
    selected_option = st.selectbox(
        "Miller Name", BASE_MILLER_LIST, key=f"ms_{unique_key}"
    )

    final_miller_name = selected_option
    if selected_option == "Other":
        custom_name = st.text_input(
            "Enter New Miller Name Here", key=f"cs_{unique_key}"
        )
        if custom_name:
            final_miller_name = custom_name
        else:
            final_miller_name = "Other (Pending Name)"

    return final_miller_name


# --- 1. SUMMARY DASHBOARD ---
if menu == "📊 Month-wise Summary Dashboard":
    st.header("📊 Executive Month-wise Summary & Stock Dashboard")

    df_rm = load_data("raw_material")
    if df_rm.empty:
        st.info("Pehle kuch data entries karein tab dashboard show hoga.")
    else:
        df_rm["Month-Year"] = pd.to_datetime(df_rm["rm_date"]).dt.strftime(
            "%B %Y"
        )
        selected_month = st.selectbox(
            "Filter by Month-Year", ["All"] + list(df_rm["Month-Year"].unique())
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

        # Milling Filter
        f_mil = load_data("milling")
        if not f_mil.empty:
            if selected_miller != "All":
                f_mil = f_mil[f_mil["miller_name"] == selected_miller]
        tot_milled = (
            f_mil["milling_qty"].sum() if not f_mil.empty else 0.0
        )

        # Finished Goods Filter
        f_fg = load_data("finished_goods")
        if not f_fg.empty:
            if selected_miller != "All":
                f_fg = f_fg[f_fg["miller_name"] == selected_miller]
        tot_finished = (
            f_fg["total_finished_qty"].sum() if not f_fg.empty else 0.0
        )

        # Dispatch Filter
        f_disp = load_data("dispatch")
        if not f_disp.empty:
            if selected_miller != "All":
                f_disp = f_disp[f_disp["miller_name"] == selected_miller]
        tot_dispatched = (
            f_disp["total_dispatched_wt"].sum()
            if not f_disp.empty
            else 0.0
        )

        closing_stock = tot_finished - tot_dispatched

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Net RM (kg)", f"{tot_net_rm:,.2f}")
        c2.metric("Total Milled (kg)", f"{tot_milled:,.2f}")
        c3.metric("Total Finished (kg)", f"{tot_finished:,.2f}")
        c4.metric("Total Dispatched (kg)", f"{tot_dispatched:,.2f}")
        c5.metric("Miller Closing Stock (kg)", f"{closing_stock:,.2f}")

        st.divider()
        st.subheader("Raw Material Overview Table")
        display_df = (
            f_rm.drop(columns=["id"]) if "id" in f_rm.columns else f_rm
        )
        st.dataframe(display_df, use_container_width=True)

# --- 2. RAW MATERIAL RECEIVED ---
elif menu == "📥 1. Raw Material Received":
    st.header("📥 Raw Material Received Entry")
    miller_name = get_miller_input("rm")

    with st.form("rm_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            rm_date = str(st.date_input("RM Date", datetime.date.today()))
            vendor_name = st.text_input("Vendor Name", value="")
            vehicle_no = st.text_input(
                "Vehicle Number", placeholder="e.g. UP-75-AT-5079"
            )
        with c2:
            hecto_wt = st.number_input(
                "Hectoliter Weight", min_value=0.0, value=0.0, step=0.1
            )
            moisture_rm = st.number_input(
                "Moisture % (RM)", min_value=0.0, value=0.0, step=0.1
            )
            broken_pct = st.number_input(
                "Broken %", min_value=0.0, value=0.0, step=0.1
            )
        with c3:
            infestation = st.selectbox(
                "Infestation", ["Nil", "Low", "Medium", "High"]
            )
            jute_bags = st.number_input(
                "Number of Jute Bags (650g fix)",
                min_value=0,
                value=0,
                step=1,
            )
            gross_qty = st.number_input(
                "Gross Qty (kg)", min_value=0.0, value=0.0, step=10.0
            )

        remarks = st.text_input("Remarks", value="")
        submit_rm = st.form_submit_button(
            label="Save Raw Material & Reset Form"
        )

        if submit_rm:
            jute_wt = jute_bags * 0.650
            net_wt = gross_qty - jute_wt
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO raw_material (rm_date, miller_name, vendor_name, vehicle_number, hectoliter_weight, moisture_rm, broken_pct, infestation, jute_bags, gross_qty, jute_weight, net_weight, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"✅ RM Saved & Permanently Stored for {miller_name}! Net Weight:"
                f" {net_wt:,.2f} kg"
            )

    st.subheader("Saved Raw Material Entries")
    df_rm_saved = load_data("raw_material")
    if not df_rm_saved.empty:
        st.dataframe(
            df_rm_saved.drop(columns=["id"])
            if "id" in df_rm_saved.columns
            else df_rm_saved,
            use_container_width=True,
        )

# --- 3. MILLING & PROCESSING ---
elif menu == "⚙️ 2. Milling & Processing":
    st.header("⚙️ Milling & Processing Entry")
    miller_name = get_miller_input("milling")

    with st.form("milling_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            milling_date = str(
                st.date_input("Milling Date", datetime.date.today())
            )
            milling_qty = st.number_input(
                "Milling Quantity (kg)", min_value=0.0, value=0.0, step=10.0
            )
        with c2:
            tempering_time = st.text_input("Tempering Time", value="")
            tempering_water = st.number_input(
                "Tempering Water (Ltr)", min_value=0.0, value=0.0, step=10.0
            )

        submit_mil = st.form_submit_button(
            label="Save Milling Data & Reset Form"
        )
        if submit_mil:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO milling (milling_date, miller_name, milling_qty, tempering_time, tempering_water)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    milling_date,
                    miller_name,
                    milling_qty,
                    tempering_time,
                    tempering_water,
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"✅ Milling Data Saved Permanently for {miller_name}!"
            )

    st.subheader("Saved Milling Entries")
    df_mil_saved = load_data("milling")
    if not df_mil_saved.empty:
        st.dataframe(
            df_mil_saved.drop(columns=["id"])
            if "id" in df_mil_saved.columns
            else df_mil_saved,
            use_container_width=True,
        )

# --- 4. QUALITY LAB PARAMETERS ---
elif menu == "🧪 3. Quality Lab Parameters":
    st.header("🧪 Quality Lab Parameters Entry")
    miller_name = get_miller_input("quality")

    with st.form("quality_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            q_date = str(st.date_input("Lab Test Date", datetime.date.today()))
            moisture_milled = st.number_input(
                "Moisture % (Milled)", min_value=0.0, value=0.0, step=0.1
            )
            granulation = st.text_input("Granulation", value="")
        with c2:
            ccl4 = st.text_input("CCL4", value="")
            ash_aia = st.number_input(
                "Ash + AIA", min_value=0.0, value=0.0, step=0.01
            )
            alcoholic_acidity = st.number_input(
                "Alcoholic Acidity", min_value=0.0, value=0.0, step=0.005
            )
        with c3:
            gluten = st.text_input("Gluten", value="")
            chapati_sensory = st.selectbox(
                "Chapati Sensory", ["Excellent", "Good", "Average", "Poor"]
            )

        submit_q = st.form_submit_button(label="Save Quality Data & Reset Form")
        if submit_q:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO quality (date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, gluten, chapati_sensory)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    q_date,
                    miller_name,
                    moisture_milled,
                    granulation,
                    ccl4,
                    ash_aia,
                    alcoholic_acidity,
                    gluten,
                    chapati_sensory,
                ),
            )
            conn.commit()
            conn.close()
            st.success("✅ Quality Test Parameters Saved Permanently!")

    st.subheader("Saved Quality Lab Records")
    df_q_saved = load_data("quality")
    if not df_q_saved.empty:
        st.dataframe(
            df_q_saved.drop(columns=["id"])
            if "id" in df_q_saved.columns
            else df_q_saved,
            use_container_width=True,
        )

# --- 5. FINISHED GOODS & YIELD ---
elif menu == "📦 4. Finished Goods & Yield":
    st.header("📦 Finished Goods, SKU Pouches & Yield Calculation")
    miller_name = get_miller_input("fg")

    with st.form("fg_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            prod_date = str(
                st.date_input("Production Date", datetime.date.today())
            )
            mfd_date = str(st.date_input("MFD Date", datetime.date.today()))
        with c2:
            expiry_date = str(
                st.date_input(
                    "Expiry Date",
                    datetime.date.today() + datetime.timedelta(days=90),
                )
            )
            mrp = st.number_input(
                "MRP (₹ per unit)", min_value=0.0, value=0.0, step=5.0
            )
        with c3:
            product_code = st.text_input("Product Code", value="")
            pouch_500g = st.number_input(
                "500gm Pouches Count", min_value=0, value=0, step=10
            )
            pouch_1kg = st.number_input(
                "1kg Pouches Count", min_value=0, value=0, step=10
            )
        with c4:
            pouch_2kg = st.number_input(
                "2kg Pouches Count", min_value=0, value=0, step=10
            )
            pouch_5kg = st.number_input(
                "5kg Pouches Count", min_value=0, value=0, step=10
            )

        st.divider()
        lc1, lc2 = st.columns(2)
        with lc1:
            bran_qty = st.number_input(
                "Bran Qty (kg)", min_value=0.0, value=0.0, step=1.0
            )
        with lc2:
            refraction_qty = st.number_input(
                "Refraction Qty (kg)", min_value=0.0, value=0.0, step=1.0
            )

        submit_fg = st.form_submit_button(
            label="Calculate Yield & Save Finished Goods"
        )
        if submit_fg:
            total_fin_qty = (
                (pouch_500g * 0.5)
                + (pouch_1kg * 1.0)
                + (pouch_2kg * 2.0)
                + (pouch_5kg * 5.0)
            )
            mil_df = load_data("milling")
            matching_milling_qty = total_fin_qty / 0.93
            if not mil_df.empty:
                miller_mills = mil_df[mil_df["miller_name"] == miller_name]
                if not miller_mills.empty:
                    matching_milling_qty = miller_mills["milling_qty"].iloc[-1]

            base_calc_qty = (
                matching_milling_qty if matching_milling_qty > 0 else 1.0
            )
            bran_pct = (bran_qty / base_calc_qty) * 100
            refraction_pct = (refraction_qty / base_calc_qty) * 100
            yield_pct = (
                (total_fin_qty / base_calc_qty) * 100
                if base_calc_qty > 0
                else 0.0
            )
            processing_loss_pct = max(
                0.0, 100.0 - (yield_pct + bran_pct + refraction_pct)
            )

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO finished_goods (production_date, miller_name, mfd_date, expiry_date, mrp, product_code, pouch_500g, pouch_1kg, pouch_2kg, pouch_5kg, total_finished_qty, bran_qty, bran_pct, refraction_qty, refraction_pct, yield_pct, processing_loss_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    prod_date,
                    miller_name,
                    mfd_date,
                    expiry_date,
                    mrp,
                    product_code,
                    pouch_500g,
                    pouch_1kg,
                    pouch_2kg,
                    pouch_5kg,
                    round(total_fin_qty, 2),
                    bran_qty,
