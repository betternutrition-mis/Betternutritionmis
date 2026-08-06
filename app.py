import datetime
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Better Nutrition & Flour Mill ERP", layout="wide"
)

st.markdown(
    "<h1 style='text-align: center; color: #2E7D32;'>BETTER NUTRITION & FLOUR"
    " MILL ERP</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #555; font-size: 16px;'>Permanent"
    " Modular Enterprise MIS with SQLite Storage</p>",
    unsafe_allow_html=True,
)
st.divider()


def check_password():
    def password_entered():
        entered_pwd = st.session_state["password"]
        if entered_pwd == "Rishabh@1994":
            st.session_state["password_correct"] = True
            st.session_state["role"] = "Admin"
            del st.session_state["password"]
        elif entered_pwd == "team123":
            st.session_state["password_correct"] = True
            st.session_state["role"] = "Team"
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password daliye app kholne ke liye:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password daliye app kholne ke liye:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("Password galat hai. Dobara koshish karein.")
        return False
    else:
        return True


if not check_password():
    st.stop()

user_role = st.session_state.get("role", "Team")
st.sidebar.write(f"Logged in as: **{user_role}**")

BASE_MILLER_LIST = [
    "Shree Balram Agro",
    "IKON ORG.",
    "Sathvik Agro",
    "Satya Naraian Kesho",
    "Tara Grains",
    "Other",
]


def get_connection():
    return sqlite3.connect("flour_mill_erp.db", check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT, rm_date TEXT, miller_name TEXT, vendor_name TEXT, vehicle_number TEXT, hectoliter_weight REAL, moisture_rm REAL, broken_pct REAL, infestation TEXT, jute_bags INTEGER, gross_qty REAL, jute_weight REAL, net_weight REAL, remarks TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milling (
            id INTEGER PRIMARY KEY AUTOINCREMENT, milling_date TEXT, miller_name TEXT, milling_qty REAL, tempering_time TEXT, tempering_water REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, miller_name TEXT, moisture_milled REAL, granulation TEXT, ccl4 TEXT, ash_aia REAL, alcoholic_acidity REAL, gluten TEXT, chapati_sensory TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finished_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT, production_date TEXT, miller_name TEXT, mfd_date TEXT, expiry_date TEXT, mrp REAL, product_code TEXT, pouch_500g INTEGER, pouch_1kg INTEGER, pouch_2kg INTEGER, pouch_5kg INTEGER, total_finished_qty REAL, bran_qty REAL, bran_pct TEXT, refraction_qty REAL, refraction_pct TEXT, yield_pct TEXT, processing_loss_pct TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packing_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, miller_name TEXT, carton_type TEXT, cartons_sent INTEGER, tape_sent INTEGER, oxysorb_qty INTEGER, roll_sku TEXT, roll_qty_sent INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatch (
            id INTEGER PRIMARY KEY AUTOINCREMENT, dispatch_date TEXT, miller_name TEXT, vehicle_no TEXT, disp_500g INTEGER, disp_1kg INTEGER, disp_2kg INTEGER, disp_5kg INTEGER, total_dispatched_wt REAL, cartons_used INTEGER, remarks TEXT
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


menu = st.sidebar.selectbox(
    "Navigation Menu",
    [
        "Month-wise Summary Dashboard",
        "1. Raw Material Received",
        "2. Milling & Processing",
        "3. Quality Lab Parameters",
        "4. Finished Goods & Yield",
        "5. Better Nutrition Packing Material",
        "6. Daily Dispatch Entry",
        "7. Master Records & Export (Admin Controls)",
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


if menu == "Month-wise Summary Dashboard":
    st.header("Executive Month-wise Summary & Stock Dashboard")
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

        # 1. Raw Material Filtered
        f_rm = df_rm.copy()
        if selected_month != "All":
            f_rm = f_rm[f_rm["Month-Year"] == selected_month]
        if selected_miller != "All":
            f_rm = f_rm[f_rm["miller_name"] == selected_miller]
        tot_net_rm = f_rm["net_weight"].sum()

        # 2. Milling Filtered by Month & Miller
        df_mil = load_data("milling")
        if not df_mil.empty:
            df_mil["Month-Year"] = pd.to_datetime(
                df_mil["milling_date"]
            ).dt.strftime("%B %Y")
        f_mil = df_mil.copy()
        if not f_mil.empty:
            if selected_month != "All":
                f_mil = f_mil[f_mil["Month-Year"] == selected_month]
            if selected_miller != "All":
                f_mil = f_mil[f_mil["miller_name"] == selected_miller]
        tot_milled = (
            f_mil["milling_qty"].sum() if not f_mil.empty else 0.0
        )

        # 3. Finished Goods Filtered by Month & Miller
        df_fg = load_data("finished_goods")
        if not df_fg.empty:
            df_fg["Month-Year"] = pd.to_datetime(
                df_fg["production_date"]
            ).dt.strftime("%B %Y")
        f_fg = df_fg.copy()
        if not f_fg.empty:
            if selected_month != "All":
                f_fg = f_fg[f_fg["Month-Year"] == selected_month]
            if selected_miller != "All":
                f_fg = f_fg[f_fg["miller_name"] == selected_miller]
        tot_finished = (
            f_fg["total_finished_qty"].sum() if not f_fg.empty else 0.0
        )

        # 4. Dispatch Filtered by Month & Miller
        df_disp = load_data("dispatch")
        if not df_disp.empty:
            df_disp["Month-Year"] = pd.to_datetime(
                df_disp["dispatch_date"]
            ).dt.strftime("%B %Y")
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
        st.dataframe(
            f_rm.drop(columns=["Month-Year"])
            if "Month-Year" in f_rm.columns
            else f_rm,
            use_container_width=True,
        )

elif menu == "1. Raw Material Received":
    st.header("Raw Material Received Entry")
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
                f"RM Saved & Permanently Stored for {miller_name}! Net Weight:"
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

elif menu == "2. Milling & Processing":
    st.header("Milling & Processing Entry")
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
                f"Milling Data Saved Permanently for {miller_name}!"
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

elif menu == "3. Quality Lab Parameters":
    st.header("Quality Lab Parameters Entry")
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
            st.success("Quality Test Parameters Saved Permanently!")

    st.subheader("Saved Quality Lab Records")
    df_q_saved = load_data("quality")
    if not df_q_saved.empty:
        st.dataframe(
            df_q_saved.drop(columns=["id"])
            if "id" in df_q_saved.columns
            else df_q_saved,
            use_container_width=True,
        )

elif menu == "4. Finished Goods & Yield":
    st.header("Finished Goods, SKU Pouches & Yield Calculation")
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
                "MRP (per unit)", min_value=0.0, value=0.0, step=5.0
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
                    f"{bran_pct:.2f}%",
                    refraction_qty,
                    f"{refraction_pct:.2f}%",
                    f"{yield_pct:.2f}%",
                    f"{processing_loss_pct:.2f}%",
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"FG Saved Permanently for {miller_name}! Total Finished:"
                f" {total_fin_qty:,.2f} kg | Yield: {yield_pct:.2f}%"
            )

    st.subheader("Saved Finished Goods Entries")
    df_fg_saved = load_data("finished_goods")
    if not df_fg_saved.empty:
        st.dataframe(
            df_fg_saved.drop(columns=["id"])
            if "id" in df_fg_saved.columns
            else df_fg_saved,
            use_container_width=True,
        )

elif menu == "5. Better Nutrition Packing Material":
    st.header("Better Nutrition - Packing Material Dispatch Entry")
    miller_name = get_miller_input("pm")
    with st.form("pm_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            pm_date = str(st.date_input("Date Sent", datetime.date.today()))
            carton_type = st.text_input(
                "Carton Type / Size", placeholder="e.g. 5kg Heavy Box"
            )
        with c2:
            cartons_sent = st.number_input(
                "Number of Cartons Sent", min_value=0, value=0, step=1
            )
            tape_sent = st.number_input(
                "Number of Tape Rolls", min_value=0, value=0, step=1
            )
        with c3:
            oxysorb_sent = st.number_input(
                "Oxysorb Qty", min_value=0, value=0, step=10
            )
            roll_sku = st.selectbox(
                "Roll SKU Type", ["500gm Roll", "1kg Roll", "2kg Roll", "5kg Roll"]
            )
            roll_qty_sent = st.number_input(
                "Roll Qty Sent", min_value=0, value=0, step=5
            )

        submit_pm = st.form_submit_button(
            label="Save Packing Material Data & Reset"
        )
        if submit_pm:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO packing_material (date, miller_name, carton_type, cartons_sent, tape_sent, oxysorb_qty, roll_sku, roll_qty_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pm_date,
                    miller_name,
                    carton_type,
                    cartons_sent,
                    tape_sent,
                    oxysorb_sent,
                    roll_sku,
                    roll_qty_sent,
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Packing Material Record Saved Permanently for"
                f" {miller_name}!"
            )

    st.subheader("Saved Packing Material Sent History")
    df_pm_saved = load_data("packing_material")
    if not df_pm_saved.empty:
        st.dataframe(
            df_pm_saved.drop(columns=["id"])
            if "id" in df_pm_saved.columns
            else df_pm_saved,
            use_container_width=True,
        )

elif menu == "6. Daily Dispatch Entry":
    st.header("Daily Finished Goods Dispatch Entry")
    miller_name = get_miller_input("dispatch")
    with st.form("dispatch_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            dispatch_date = str(
                st.date_input("Dispatch Date", datetime.date.today())
            )
            vehicle_no = st.text_input(
                "Vehicle No", placeholder="e.g. UP-32-XX-1234"
            )
        with c2:
            disp_500g = st.number_input(
                "Dispatched 500gm Pouches", min_value=0, value=0, step=10
            )
            disp_1kg = st.number_input(
                "Dispatched 1kg Pouches", min_value=0, value=0, step=10
            )
            disp_2kg = st.number_input(
                "Dispatched 2kg Pouches", min_value=0, value=0, step=10
            )
        with c3:
            disp_5kg = st.number_input(
                "Dispatched 5kg Pouches", min_value=0, value=0, step=10
            )
            cartons_used = st.number_input(
                "Cartons Used (Minus from Stock)",
                min_value=0,
                value=0,
                step=1,
            )
        remarks = st.text_input("Remarks", value="")
        submit_disp = st.form_submit_button(
            label="Save Dispatch Data & Reset Form"
        )
        if submit_disp:
            tot_disp_wt = (
                (disp_500g * 0.5)
                + (disp_1kg * 1.0)
                + (disp_2kg * 2.0)
                + (disp_5kg * 5.0)
            )
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dispatch (dispatch_date, miller_name, vehicle_no, disp_500g, disp_1kg, disp_2kg, disp_5kg, total_dispatched_wt, cartons_used, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    dispatch_date,
                    miller_name,
                    vehicle_no,
                    disp_500g,
                    disp_1kg,
                    disp_2kg,
                    disp_5kg,
                    round(tot_disp_wt, 2),
                    cartons_used,
                    remarks,
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Dispatch Saved Permanently for {miller_name}! Total"
                f" Dispatched Wt: {tot_disp_wt:,.2f} kg"
            )

    st.subheader("Saved Dispatch History")
    df_disp_saved = load_data("dispatch")
    if not df_disp_saved.empty:
        st.dataframe(
            df_disp_saved.drop(columns=["id"])
            if "id" in df_disp_saved.columns
            else df_disp_saved,
            use_container_width=True,
        )

elif menu == "7. Master Records & Export (Admin Controls)":
    st.header("Complete Permanent Master Database & Admin Controls")
    if st.session_state.get("role") != "Admin":
        st.error(
            "Yeh section sirf Admin ke liye hai! Aapne 'Team' password"
            " se login kiya hai, isliye yahan edit/delete controls hidden"
            " hain."
        )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Raw Material",
            "Milling",
            "Quality Lab",
            "Finished Goods",
            "Packing Material",
            "Dispatch",
        ]
    )


    def handle_admin_table_view(table_name, report_title, file_name):
        df = load_data(table_name)
        if df.empty:
            st.info("No data found.")
            return
        st.download_button(
            f"Download {report_title} CSV",
            df.drop(columns=["id"]).to_csv(index=False).encode("utf-8"),
            file_name,
            "text/csv",
        )
        st.divider()

        if st.session_state.get("role") == "Admin":
            st.subheader(f"Manage {report_title} Records (Admin Edit & Delete)")
            for index, row in df.iterrows():
                row_id = row["id"]
                date_val = row.get(
                    "rm_date",
                    row.get(
                        "milling_date",
                        row.get("date", row.get("production_date", "")),
                    ),
                )
                miller_val = row.get("miller_name", "")
                with st.expander(
                    f"ID: {row_id} | Date: {date_val} | Miller: {miller_val}"
                ):
                    edit_mode_key = f"edit_mode_{table_name}_{row_id}"
                    if edit_mode_key not in st.session_state:
                        st.session_state[edit_mode_key] = False

                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button(
                            "Edit Record", key=f"btn_edit_{table_name}_{row_id}"
                        ):
                            st.session_state[edit_mode_key] = (
                                not st.session_state[edit_mode_key]
                            )
                            st.rerun()
                    with c_btn2:
                        del_confirm_key = (
                            f"del_confirm_{table_name}_{row_id}"
                        )
                        if del_confirm_key not in st.session_state:
                            st.session_state[del_confirm_key] = False
                        if not st.session_state[del_confirm_key]:
                            if st.button(
                                "Delete", key=f"btn_del_{table_name}_{row_id}"
                            ):
                                st.session_state[del_confirm_key] = True
                                st.rerun()
                        else:
                            st.warning(
                                "Kya aap sach mein is entry ko delete"
                                " karna chahte hain?"
                            )
                            yb1, yb2 = st.columns(2)
                            with yb1:
                                if st.button(
                                    "Haan, Delete Karo",
                                    key=f"confirm_del_{table_name}_{row_id}",
                                ):
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        f"DELETE FROM {table_name} WHERE id = ?",
                                        (row_id,),
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.session_state[del_confirm_key] = False
                                    st.success(
                                        f"Deleted ID {row_id} successfully!"
                                    )
                                    st.rerun()
                            with yb2:
                                if st.button(
                                    "Nahi, Rehne Do",
                                    key=f"cancel_del_{table_name}_{row_id}",
                                ):
                                    st.session_state[del_confirm_key] = False
                                    st.rerun()

                    if st.session_state[edit_mode_key]:
                        st.write(f"**Editing ID {row_id}**")
                        with st.form(key=f"update_form_{table_name}_{row_id}"):
                            updated_data = {}
                            for col_name in df.columns:
                                if col_name == "id":
                                    continue
                                val = row[col_name]
                                if isinstance(val, (int, float)):
                                    updated_data[col_name] = st.number_input(
                                        col_name, value=float(val)
                                    )
                                else:
                                    updated_data[col_name] = st.text_input(
                                        col_name, value=str(val)
                                    )
                            update_submit = st.form_submit_button(
                                "Save Changes (Update)"
                            )
                            if update_submit:
                                conn = get_connection()
                                cursor = conn.cursor()
                                set_clause = ", ".join(
                                    [f"{k} = ?" for k in updated_data.keys()]
                                )
                                values = list(updated_data.values()) + [
                                    row_id
                                ]
                                cursor.execute(
                                    f"UPDATE {table_name} SET {set_clause} WHERE id = ?",
                                    values,
                                )
                                conn.commit()
                                conn.close()
                                st.session_state[edit_mode_key] = False
                                st.success(
                                    f"ID {row_id} updated successfully!"
                                )
                                st.rerun()
            st.divider()
        st.subheader(f"Full {report_title} Table View")
        st.dataframe(
            df.drop(columns=["id"]) if "id" in df.columns else df,
            use_container_width=True,
        )

    with tab1:
        handle_admin_table_view(
            "raw_material", "Raw Material", "rm_report.csv"
        )
    with tab2:
        handle_admin_table_view("milling", "Milling", "milling_report.csv")
    with tab3:
        handle_admin_table_view("quality", "Quality Lab", "quality_report.csv")
    with tab4:
        handle_admin_table_view(
            "finished_goods", "Finished Goods", "fg_report.csv"
        )
    with tab5:
        handle_admin_table_view(
            "packing_material",
            "Packing Material",
            "packing_material_report.csv",
        )
    with tab6:
        handle_admin_table_view("dispatch", "Dispatch", "dispatch_report.csv")
