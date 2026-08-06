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
            id INTEGER PRIMARY KEY AUTOINCREMENT, milling_id INTEGER, test_date TEXT, miller_name TEXT, moisture_milled REAL, granulation TEXT, ccl4 TEXT, ash_aia REAL, alcoholic_acidity REAL, wap REAL, gluten TEXT, chapati_sensory TEXT
        )
    """)
    try:
        cursor.execute("ALTER TABLE quality ADD COLUMN wap REAL")
    except Exception:
        pass

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
    st.header("Executive Month-wise Summary & Stock Dashboard")
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
    st.header("Raw Material Received Entry")

    if "edit_rm_id" not in st.session_state:
        st.session_state["edit_rm_id"] = None

    df_rm_saved = load_data("raw_material")

    if not df_rm_saved.empty:
        action_type = st.radio(
            "Action Mode", ["➕ New Entry", "✏️ Edit / 🗑️ Delete Existing Entry"], horizontal=True
        )
    else:
        action_type = "➕ New Entry"

    edit_data = None
    if action_type == "✏️ Edit / 🗑️ Delete Existing Entry" and not df_rm_saved.empty:
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
            "Select Raw Material Record to Modify/Delete", df_rm_saved["label"].tolist()
        )
        selected_row = df_rm_saved[df_rm_saved["label"] == selected_row_label].iloc[0]
        st.session_state["edit_rm_id"] = int(selected_row["id"])
        edit_data = selected_row

        with st.expander("⚠️ Delete Confirmation Box", expanded=True):
            confirm_del = st.checkbox("Haan, main is record ko permanently delete karna chahta hoon", key="conf_del_rm")
            if st.button("🗑️ Confirm & Delete Record", type="primary"):
                if confirm_del:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM raw_material WHERE id = ?", (st.session_state["edit_rm_id"],)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Record ID {st.session_state['edit_rm_id']} successfully deleted!")
                    st.session_state["edit_rm_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        st.session_state["edit_rm_id"] = None

    if action_type == "➕ New Entry" or st.session_state["edit_rm_id"] is not None:
        default_miller = edit_data["miller_name"] if edit_data is not None else None
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
                    "Vehicle Number", value=default_veh, placeholder="e.g. UP-75-AT-5079"
                )
            with c2:
                default_hecto = (
                    float(edit_data["hectoliter_weight"])
                    if edit_data is not None
                    else 0.0
                )
                hecto_wt = st.number_input(
                    "Hectoliter Weight", min_value=0.0, value=default_hecto, step=0.1, format="%.1f"
                )

                default_mois = (
                    float(edit_data["moisture_rm"])
                    if edit_data is not None
                    else 0.0
                )
                moisture_rm = st.number_input(
                    "Moisture % (RM)", min_value=0.0, value=default_mois, step=0.1, format="%.1f"
                )

                default_broken = (
                    float(edit_data["broken_pct"])
                    if edit_data is not None
                    else 0.0
                )
                broken_pct = st.number_input(
                    "Broken %", min_value=0.0, value=default_broken, step=0.1, format="%.1f"
                )
            with c3:
                infestation_opts = ["Nil", "Low", "Medium", "High"]
                default_inf_idx = 0
                if edit_data is not None and edit_data["infestation"] in infestation_opts:
                    default_inf_idx = infestation_opts.index(edit_data["infestation"])
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
                    float(edit_data["gross_qty"]) if edit_data is not None else 0.0
                )
                gross_qty = st.number_input(
                    "Gross Qty (kg)", min_value=0.0, value=default_gross, step=10.0, format="%.2f"
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
                    st.success(f"Raw Material Record ID {st.session_state['edit_rm_id']} Updated Successfully!")
                    st.session_state["edit_rm_id"] = None
                    st.rerun()
                else:
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
    df_rm_saved_display = load_data("raw_material")
    if not df_rm_saved_display.empty:
        st.dataframe(df_rm_saved_display, use_container_width=True)

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
                    "Milling Quantity (kg)", value=None, placeholder="Type qty...", step=10.0
                )
            with c2:
                tempering_time = st.text_input("Tempering Time", value="")
                tempering_water = st.number_input(
                    "Tempering Water (Ltr)", value=None, placeholder="Type water...", step=10.0
                )

            st.divider()
            st.subheader("2. Quality Lab Parameters")
            qc1, qc2, qc3 = st.columns(3)
