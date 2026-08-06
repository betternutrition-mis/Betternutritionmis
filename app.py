import datetime
import os
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
            id INTEGER PRIMARY KEY AUTOINCREMENT, milling_id INTEGER, test_date TEXT, miller_name TEXT, moisture_milled REAL, granulation TEXT, ccl4 TEXT, ash_aia REAL, alcoholic_acidity REAL, gluten TEXT, chapati_sensory TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finished_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT, milling_id INTEGER, production_date TEXT, miller_name TEXT, mfd_date TEXT, expiry_date TEXT, mrp REAL, product_code TEXT, pouch_500g INTEGER, pouch_1kg INTEGER, pouch_2kg INTEGER, pouch_5kg INTEGER, total_finished_qty REAL, bran_qty REAL, bran_pct TEXT, refraction_qty REAL, refraction_pct TEXT, yield_pct TEXT, processing_loss_pct TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packing_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, miller_name TEXT, carton_type TEXT, cartons_sent INTEGER, tape_sent INTEGER, oxysorb_qty INTEGER, roll_sku TEXT, roll_qty_sent REAL
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
        df_rm["Parsed_Date"] = pd.to_datetime(df_rm["rm_date"], errors="coerce")
        df_rm["Month-Year"] = df_rm["Parsed_Date"].dt.strftime("%B %Y")
        selected_month = st.selectbox(
            "Filter by Month-Year", ["All"] + list(df_rm["Month-Year"].dropna().unique())
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
            df_mil["Parsed_Date"] = pd.to_datetime(df_mil["milling_date"], errors="coerce")
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
            df_fg["Parsed_Date"] = pd.to_datetime(df_fg["production_date"], errors="coerce")
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
            df_disp["Parsed_Date"] = pd.to_datetime(df_disp["dispatch_date"], errors="coerce")
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
        cols_to_drop = [c for c in ["Month-Year", "Parsed_Date"] if c in f_rm.columns]
        st.dataframe(
            f_rm.drop(columns=cols_to_drop),
            use_container_width=True,
        )

elif menu == "1. Raw Material Received":
    st.header("Raw Material Received Entry")
    miller_name = get_miller_input("rm")
    with st.form("rm_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            raw_date_obj = st.date_input("RM Date", datetime.date.today())
            rm_date = raw_date_obj.strftime("%d %b %Y")
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

elif menu == "2. Milling & Quality Lab Entry":
    st.header("Milling Processing & Quality Lab Entry")

    tab_new, tab_update_old = st.tabs(
        [
            "➕ New Milling & Quality Entry",
            "🛠️ Update Quality for Old Milling Batches",
        ]
    )

    with tab_new:
        miller_name = get_miller_input("milling_q")
        with st.form("milling_quality_form", clear_on_submit=True):
            st.subheader("1. Milling Parameters")
            c1, c2 = st.columns(2)
            with c1:
                mil_date_obj = st.date_input("Milling Date", datetime.date.today())
                milling_date = mil_date_obj.strftime("%d %b %Y")
                milling_qty = st.number_input(
                    "Milling Quantity (kg)", min_value=0.0, value=0.0, step=10.0
                )
            with c2:
                tempering_time = st.text_input("Tempering Time", value="")
                tempering_water = st.number_input(
                    "Tempering Water (Ltr)", min_value=0.0, value=0.0, step=10.0
                )

            st.divider()
            st.subheader("2. Quality Lab Parameters")
            qc1, qc2, qc3 = st.columns(3)
            with qc1:
                q_date_obj = st.date_input("Lab Test Date", datetime.date.today())
                q_date = q_date_obj.strftime("%d %b %Y")
                moisture_milled = st.number_input(
                    "Moisture % (Milled)",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                )
                granulation = st.text_input("Granulation", value="")
            with qc2:
                ccl4 = st.text_input("CCL4", value="")
                ash_aia = st.number_input(
                    "Ash + AIA", min_value=0.0, value=0.0, step=0.01
                )
                alcoholic_acidity = st.number_input(
                    "Alcoholic Acidity", min_value=0.0, value=0.0, step=0.005
                )
            with qc3:
                gluten = st.text_input("Gluten", value="")
                chapati_sensory = st.selectbox(
                    "Chapati Sensory",
                    ["Excellent", "Good", "Average", "Poor"],
                )

            submit_both = st.form_submit_button(
                label="Save Milling & Quality Data"
            )
            if submit_both:
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
                milling_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, gluten, chapati_sensory)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        milling_id,
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
                st.success(
                    f"Milling & Quality Data Successfully Saved for {miller_name}!"
                )
                st.rerun()

    with tab_update_old:
        st.subheader(
            "Purane Milling Batches Jinme Quality Data Nahi Hai, Unko Update"
            " Karein"
        )
        df_mil = load_data("milling")
        df_q = load_data("quality")

        if df_mil.empty:
            st.info("Koi milling record nahi mila.")
        else:
            tested_ids = (
                df_q["milling_id"].tolist()
                if not df_q.empty and "milling_id" in df_q.columns
                else []
            )
            untested_mil = df_mil[~df_mil["id"].isin(tested_ids)]

            if untested_mil.empty:
                st.success(
                    "Sabhi purane milling batches ki quality entry pehle se ho"
                    " chuki hai!"
                )
            else:
                untested_mil["label"] = (
                    "Batch ID: "
                    + untested_mil["id"].astype(str)
                    + " | Miller: "
                    + untested_mil["miller_name"]
                    + " | Date: "
                    + untested_mil["milling_date"]
                    + " | Qty: "
                    + untested_mil["milling_qty"].astype(str)
                    + " kg"
                )
                sel_batch = st.selectbox(
                    "Select Untested Milling Batch", untested_mil["label"].tolist()
                )
                sel_row = untested_mil[
                    untested_mil["label"] == sel_batch
                ].iloc[0]
                target_m_id = int(sel_row["id"])
                t_miller = sel_row["miller_name"]

                with st.form("update_old_q_form"):
                    st.write(
                        f"Updating Quality for Batch ID: {target_m_id} ({t_miller})"
                    )
                    oq_date_obj = st.date_input("Lab Test Date", datetime.date.today())
                    oq_date = oq_date_obj.strftime("%d %b %Y")
                    omoisture = st.number_input(
                        "Moisture % (Milled)",
                        min_value=0.0,
                        value=0.0,
                        step=0.1,
                    )
                    ogranulation = st.text_input("Granulation", value="")
                    occl4 = st.text_input("CCL4", value="")
                    oash = st.number_input(
                        "Ash + AIA", min_value=0.0, value=0.0, step=0.01
                    )
                    oacidity = st.number_input(
                        "Alcoholic Acidity", min_value=0.0, value=0.0, step=0.005
                    )
                    ogluten = st.text_input("Gluten", value="")
                    osensory = st.selectbox(
                        "Chapati Sensory",
                        ["Excellent", "Good", "Average", "Poor"],
                    )

                    submit_old_q = st.form_submit_button(
                        "Save Quality for this Old Batch"
                    )
                    if submit_old_q:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                target_m_id,
                                oq_date,
                                t_miller,
                                omoisture,
                                ogranulation,
                                occl4,
                                oash,
                                oacidity,
                                ogluten,
                                osensory,
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.success(
                            f"Quality successfully added for Batch ID"
                            f" {target_m_id}!"
                        )
                        st.rerun()

    st.subheader("Saved Milling Records")
    df_mil_saved = load_data("milling")
    if not df_mil_saved.empty:
        st.dataframe(
            df_mil_saved.drop(columns=["id"])
            if "id" in df_mil_saved.columns
            else df_mil_saved,
            use_container_width=True,
        )

    st.subheader("Saved Quality Lab Records")
    df_q_saved = load_data("quality")
    if not df_q_saved.empty:
        st.dataframe(
            df_q_saved.drop(columns=["id", "milling_id"])
            if "id" in df_q_saved.columns
            else df_q_saved,
            use_container_width=True,
        )

elif menu == "3. Finished Goods & Yield":
    st.header("Finished Goods Production & Yield Tracking")
    df_mil = load_data("milling")
    if df_mil.empty:
        st.warning(
            "Pehle Menu 2 se Milling entry karein, tabhi Finished Goods entry"
            " ho sakegi."
        )
    else:
        df_mil["label"] = (
            "ID: "
            + df_mil["id"].astype(str)
            + " | Miller: "
            + df_mil["miller_name"]
            + " | Date: "
            + df_mil["milling_date"]
            + " | Qty: "
            + df_mil["milling_qty"].astype(str)
            + " kg"
        )
        sel_milling = st.selectbox(
            "Select Milling Batch for Finished Goods", df_mil["label"].tolist()
        )
        row_mil = df_mil[df_mil["label"] == sel_milling].iloc[0]
        milling_id = int(row_mil["id"])
        miller_name = row_mil["miller_name"]
        milling_qty = float(row_mil["milling_qty"])

        with st.form("fg_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                prod_date_obj = st.date_input("Production Date", datetime.date.today())
                production_date = prod_date_obj.strftime("%d %b %Y")
                mfd_date = st.text_input("MFD Date", placeholder="e.g. Jun 2026")
                expiry_date = st.text_input(
                    "Expiry Date", placeholder="e.g. 6 Months"
                )
            with c2:
                mrp = st.number_input("MRP (Rs)", min_value=0.0, value=0.0)
                product_code = st.text_input(
                    "Product Code / SKU", value="BN-ATTA-01"
                )
                pouch_500g = st.number_input(
                    "500g Pouches Count", min_value=0, value=0, step=1
                )
            with c3:
                pouch_1kg = st.number_input(
                    "1kg Pouches Count", min_value=0, value=0, step=1
                )
                pouch_2kg = st.number_input(
                    "2kg Pouches Count", min_value=0, value=0, step=1
                )
                pouch_5kg = st.number_input(
                    "5kg Pouches Count", min_value=0, value=0, step=1
                )

            st.divider()
            sc1, sc2 = st.columns(2)
            with sc1:
                bran_qty = st.number_input(
                    "Bran Quantity (kg)", min_value=0.0, value=0.0, step=1.0
                )
            with sc2:
                refraction_qty = st.number_input(
                    "Refraction Quantity (kg)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                )

            submit_fg = st.form_submit_button(
                label="Calculate Yield & Save Finished Goods"
            )
            if submit_fg:
                wt_500g = pouch_500g * 0.5
                wt_1kg = pouch_1kg * 1.0
                wt_2kg = pouch_2kg * 2.0
                wt_5kg = pouch_5kg * 5.0
                total_finished_qty = wt_500g + wt_1kg + wt_2kg + wt_5kg

                bran_pct = (
                    (bran_qty / milling_qty) * 100 if milling_qty > 0 else 0.0
                )
                refraction_pct = (
                    (refraction_qty / milling_qty) * 100
                    if milling_qty > 0
                    else 0.0
                )
                yield_pct = (
                    (total_finished_qty / milling_qty) * 100
                    if milling_qty > 0
                    else 0.0
                )

                total_accounted = (
                    total_finished_qty + bran_qty + refraction_qty
                )
                processing_loss_qty = milling_qty - total_accounted
                processing_loss_pct = (
                    (processing_loss_qty / milling_qty) * 100
                    if milling_qty > 0
                    else 0.0
                )

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO finished_goods (milling_id, production_date, miller_name, mfd_date, expiry_date, mrp, product_code, pouch_500g, pouch_1kg, pouch_2kg, pouch_5kg, total_finished_qty, bran_qty, bran_pct, refraction_qty, refraction_pct, yield_pct, processing_loss_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        milling_id,
                        production_date,
                        miller_name,
                        mfd_date,
                        expiry_date,
                        mrp,
                        product_code,
                        pouch_500g,
                        pouch_1kg,
                        pouch_2kg,
                        pouch_5kg,
                        round(total_finished_qty, 2),
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
                    f"Finished Goods Saved! Total Finished Output:"
                    f" {total_finished_qty:,.2f} kg | Yield:"
                    f" {yield_pct:.2f}%"
                )

    st.subheader("Saved Finished Goods Records")
    df_fg_saved = load_data("finished_goods")
    if not df_fg_saved.empty:
        st.dataframe(
            df_fg_saved.drop(columns=["id", "milling_id"])
            if "id" in df_fg_saved.columns
            else df_fg_saved,
            use_container_width=True,
        )

elif menu == "4. Better Nutrition Packing Material":
    st.header("Better Nutrition Packing Material Dispatch/Stock Entry")
    miller_name = get_miller_input("pm")
    with st.form("pm_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            pm_date_obj = st.date_input("Date", datetime.date.today())
            pm_date = pm_date_obj.strftime("%d %b %Y")
            carton_type = st.selectbox(
                "Carton Type", ["500g Carton", "1kg Carton", "2kg Carton", "5kg Carton"]
            )
            cartons_sent = st.number_input(
                "Cartons Sent (Units)", min_value=0, value=0, step=1
            )
            tape_sent = st.number_input(
                "Tape Sent (Rolls)", min_value=0, value=0, step=1
            )
        with c2:
            oxysorb_qty = st.number_input(
                "Oxysorb Packets Qty", min_value=0, value=0, step=10
            )
            roll_sku = st.text_input("Roll SKU / Description", value="")
            roll_qty_sent = st.number_input(
                "Roll Qty Sent (kg or meters)",
                min_value=0.0,
                value=0.0,
                step=1.0,
            )

        submit_pm = st.form_submit_button(
            label="Save Packing Material Entry"
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
                    oxysorb_qty,
                    roll_sku,
                    roll_qty_sent,
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Packing Material entry successfully saved for {miller_name}!"
            )

    st.subheader("Saved Packing Material Records")
    df_pm_saved = load_data("packing_material")
    if not df_pm_saved.empty:
        st.dataframe(
            df_pm_saved.drop(columns=["id"])
            if "id" in df_pm_saved.columns
            else df_pm_saved,
            use_container_width=True,
        )

elif menu == "5. Daily Dispatch Entry":
    st.header("Daily Finished Goods Dispatch Entry")
    miller_name = get_miller_input("dispatch")
    with st.form("dispatch_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            disp_date_obj = st.date_input("Dispatch Date", datetime.date.today())
            dispatch_date = disp_date_obj.strftime("%d %b %Y")
            vehicle_no = st.text_input(
                "Vehicle Number", placeholder="e.g. UP-32-XZ-1234"
            )
            disp_500g = st.number_input(
                "Dispatched 500g Pouches", min_value=0, value=0, step=1
            )
            disp_1kg = st.number_input(
                "Dispatched 1kg Pouches", min_value=0, value=0, step=1
            )
        with c2:
            disp_2kg = st.number_input(
                "Dispatched 2kg Pouches", min_value=0, value=0, step=1
            )
            disp_5kg = st.number_input(
                "Dispatched 5kg Pouches", min_value=0, value=0, step=1
            )
            cartons_used = st.number_input(
                "Cartons Used", min_value=0, value=0, step=1
            )
            remarks = st.text_input("Dispatch Remarks / Destination", value="")

        submit_disp = st.form_submit_button(
            label="Save Dispatch Entry"
        )
        if submit_disp:
            total_disp_wt = (
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
                    round(total_disp_wt, 2),
                    cartons_used,
                    remarks,
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Dispatch Saved Successfully! Total Dispatched Weight:"
                f" {total_disp_wt:,.2f} kg"
            )

    st.subheader("Saved Dispatch Records")
    df_disp_saved = load_data("dispatch")
    if not df_disp_saved.empty:
        st.dataframe(
            df_disp_saved.drop(columns=["id"])
            if "id" in df_disp_saved.columns
            else df_disp_saved,
            use_container_width=True,
        )

elif menu == "6. Master Records & Export (Admin Controls)":
    st.header("Master Records, Data Management & Admin Controls")

    if user_role != "Admin":
        st.warning(
            "⚠️ Ye section sirf **Admin** access ke liye hai. Aapka current role"
            f" '{user_role}' hai."
        )
    else:
        st.success(
            "🔓 Admin privileges active. Aap tables view kar sakte hain aur data"
            " export/delete kar sakte hain."
        )

        table_to_manage = st.selectbox(
            "Select Database Table to Manage",
            [
                "raw_material",
                "milling",
                "quality",
                "finished_goods",
                "packing_material",
                "dispatch",
            ],
        )

        df_manage = load_data(table_to_manage)
        st.write(f"### Current Data in `{table_to_manage}`")
        if df_manage.empty:
            st.info("Table khaali hai.")
        else:
            st.dataframe(df_manage, use_container_width=True)

            # CSV Download Button
            csv_data = df_manage.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Download `{table_to_manage}` as CSV",
                data=csv_data,
                file_name=f"{table_to_manage}_export.csv",
                mime="text/csv",
            )

        st.divider()
        st.subheader("Danger Zone / Database Maintenance")
        if st.button("🗑️ Delete Database File (Reset Everything)"):
            if os.path.exists("flour_mill_erp.db"):
                os.remove("flour_mill_erp.db")
                st.warning(
                    "Database file delete ho chuki hai. App ko refresh karein"
                    " naye tables banane ke liye."
                )
                st.rerun()
            else:
                st.error("Database file nahi mili.")
