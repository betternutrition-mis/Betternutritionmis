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
            "Action Mode", ["➕ New Entry", "✏️ Edit / 🗑️ Delete Existing Entry"], horizontal=True, key="mode_rm"
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
            "Select Raw Material Record to Modify/Delete", df_rm_saved["label"].tolist(), key="sel_rm_edit"
        )
        selected_row = df_rm_saved[df_rm_saved["label"] == selected_row_label].iloc[0]
        st.session_state["edit_rm_id"] = int(selected_row["id"])
        edit_data = selected_row

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del = st.checkbox("Haan, main is record ko permanently delete karna chahta hoon", key="conf_del_rm")
            if st.button("🗑️ Confirm & Delete Record", type="primary", key="btn_del_rm_rec"):
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

    if "edit_mil_id" not in st.session_state:
        st.session_state["edit_mil_id"] = None

    df_mil_saved = load_data("milling")

    action_type_mil = "➕ New Milling & Quality Entry"
    if not df_mil_saved.empty:
        action_type_mil = st.radio(
            "Action Mode", ["➕ New Milling & Quality Entry", "✏️ Edit / 🗑️ Delete Existing Milling", "🛠️ Update Quality for Old Batches"], horizontal=True, key="mode_mil"
        )
    else:
        action_type_mil = st.radio(
            "Action Mode", ["➕ New Milling & Quality Entry", "🛠️ Update Quality for Old Batches"], horizontal=True, key="mode_mil_empty"
        )

    edit_mil_data = None
    if action_type_mil == "✏️ Edit / 🗑️ Delete Existing Milling" and not df_mil_saved.empty:
        df_mil_saved["label"] = (
            "ID: " + df_mil_saved["id"].astype(str) + " | " + df_mil_saved["miller_name"] + " (" + df_mil_saved["milling_date"] + ")"
        )
        sel_edit_mil = st.selectbox("Select Milling Record to Modify/Delete", df_mil_saved["label"].tolist(), key="sel_edit_mil")
        selected_mil_row = df_mil_saved[df_mil_saved["label"] == sel_edit_mil].iloc[0]
        st.session_state["edit_mil_id"] = int(selected_mil_row["id"])
        edit_mil_data = selected_mil_row

        with st.expander("⚠️ Delete Confirmation Box (Milling)", expanded=False):
            confirm_del_mil = st.checkbox("Haan, main is milling record ko permanently delete karna chahta hoon", key="conf_del_mil")
            if st.button("🗑️ Confirm & Delete Milling Record", type="primary", key="btn_del_mil_rec"):
                if confirm_del_mil:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM milling WHERE id = ?", (st.session_state["edit_mil_id"],))
                    cursor.execute("DELETE FROM quality WHERE milling_id = ?", (st.session_state["edit_mil_id"],))
                    conn.commit()
                    conn.close()
                    st.success(f"Milling & Quality Record ID {st.session_state['edit_mil_id']} deleted successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    elif action_type_mil == "🛠️ Update Quality for Old Batches":
        st.subheader("Update/Add Quality Parameters for Existing Milling Batches")
        if df_mil_saved.empty:
            st.warning("Koi milling batch available nahi hai.")
        else:
            df_mil_saved["label"] = (
                "ID: " + df_mil_saved["id"].astype(str) + " | " + df_mil_saved["miller_name"] + " (" + df_mil_saved["milling_date"] + ")"
            )
            sel_q_batch = st.selectbox("Select Milling Batch for Quality", df_mil_saved["label"].tolist(), key="sel_q_batch_old")
            q_row = df_mil_saved[df_mil_saved["label"] == sel_q_batch].iloc[0]
            q_milling_id = int(q_row["id"])
            q_miller = q_row["miller_name"]

            df_q_existing = load_data("quality")
            q_match = df_q_existing[df_q_existing["milling_id"] == q_milling_id]
            q_exist_data = q_match.iloc[0] if not q_match.empty else None

            with st.form("old_quality_form"):
                st.write(f"**Quality Lab Test Entry for Batch ID:** {q_milling_id} ({q_miller})")
                c1, c2, c3 = st.columns(3)
                with c1:
                    q_date_val = datetime.date.today()
                    if q_exist_data is not None and pd.notna(q_exist_data["test_date"]):
                        try:
                            q_date_val = datetime.datetime.strptime(q_exist_data["test_date"], "%d %b %Y").date()
                        except Exception:
                            pass
                    test_date = st.date_input("Lab Test Date", value=q_date_val, key="old_tdate").strftime("%d %b %Y")

                    def_mo_milled = float(q_exist_data["moisture_milled"]) if q_exist_data is not None and pd.notna(q_exist_data["moisture_milled"]) else 0.0
                    moisture_milled = st.number_input("Moisture % (Milled/Atta)", min_value=0.0, value=def_mo_milled, step=0.1, format="%.1f", key="old_mo_milled")

                    def_gran = str(q_exist_data["granulation"]) if q_exist_data is not None and pd.notna(q_exist_data["granulation"]) else ""
                    granulation = st.text_input("Granulation / Fineness", value=def_gran, placeholder="e.g. Fine / 95% through 150 mesh", key="old_gran")

                with c2:
                    def_ccl4 = str(q_exist_data["ccl4"]) if q_exist_data is not None and pd.notna(q_exist_data["ccl4"]) else ""
                    ccl4 = st.text_input("CCL4 Test", value=def_ccl4, placeholder="e.g. Sound / Clean", key="old_ccl4")

                    def_ash = float(q_exist_data["ash_aia"]) if q_exist_data is not None and pd.notna(q_exist_data["ash_aia"]) else 0.0
                    ash_aia = st.number_input("Ash / AIA %", min_value=0.0, value=def_ash, step=0.01, format="%.2f", key="old_ash")

                    def_aa = float(q_exist_data["alcoholic_acidity"]) if q_exist_data is not None and pd.notna(q_exist_data["alcoholic_acidity"]) else 0.0
                    alcoholic_acidity = st.number_input("Alcoholic Acidity", min_value=0.0, value=def_aa, step=0.01, format="%.2f", key="old_aa")

                with c3:
                    def_wap = float(q_exist_data["wap"]) if q_exist_data is not None and "wap" in q_exist_data and pd.notna(q_exist_data["wap"]) else 0.0
                    wap = st.number_input("WAP (Water Absorption / Wapsi)", min_value=0.0, value=def_wap, step=0.1, format="%.1f", key="old_wap")

                    def_gluten = str(q_exist_data["gluten"]) if q_exist_data is not None and pd.notna(q_exist_data["gluten"]) else ""
                    gluten = st.text_input("Gluten %", value=def_gluten, placeholder="e.g. 9.5%", key="old_gluten")

                    def_chapati = str(q_exist_data["chapati_sensory"]) if q_exist_data is not None and pd.notna(q_exist_data["chapati_sensory"]) else ""
                    chapati_sensory = st.text_input("Chapati Sensory / Quality", value=def_chapati, placeholder="e.g. Soft, Excellent", key="old_chap")

                submit_old_q = st.form_submit_button("💾 Save / Update Quality Lab Data")
                if submit_old_q:
                    conn = get_connection()
                    cursor = conn.cursor()
                    if q_exist_data is not None:
                        cursor.execute("""
                            UPDATE quality 
                            SET test_date=?, miller_name=?, moisture_milled=?, granulation=?, ccl4=?, ash_aia=?, alcoholic_acidity=?, wap=?, gluten=?, chapati_sensory=?
                            WHERE milling_id=?
                        """, (test_date, q_miller, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory, q_milling_id))
                    else:
                        cursor.execute("""
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (q_milling_id, test_date, q_miller, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory))
                    conn.commit()
                    conn.close()
                    st.success(f"Quality details successfully updated for Batch ID {q_milling_id}!")
                    st.rerun()

    if action_type_mil == "➕ New Milling & Quality Entry" or st.session_state["edit_mil_id"] is not None:
        def_mil_miller = edit_mil_data["miller_name"] if edit_mil_data is not None else None
        milling_miller_name = get_miller_input("mil", def_mil_miller)

        with st.form("milling_quality_form"):
            st.subheader("1. Milling Details")
            c1, c2, c3 = st.columns(3)
            with c1:
                def_mdate = datetime.date.today()
                if edit_mil_data is not None:
                    try:
                        def_mdate = datetime.datetime.strptime(edit_mil_data["milling_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                m_date_obj = st.date_input("Milling Date", value=def_mdate)
                milling_date = m_date_obj.strftime("%d %b %Y")
            with c2:
                def_mqty = float(edit_mil_data["milling_qty"]) if edit_mil_data is not None else 0.0
                milling_qty = st.number_input("Milling Quantity (Wheat Input kg)", min_value=0.0, value=def_mqty, step=10.0, format="%.2f")
            with c3:
                def_temp_time = edit_mil_data["tempering_time"] if edit_mil_data is not None and "tempering_time" in edit_mil_data else ""
                tempering_time = st.text_input("Tempering Time", value=def_temp_time, placeholder="e.g. 12 Hours")

            def_temp_water = float(edit_mil_data["tempering_water"]) if edit_mil_data is not None and "tempering_water" in edit_mil_data and pd.notna(edit_mil_data["tempering_water"]) else 0.0
            tempering_water = st.number_input("Tempering Water Added (liters/kg)", min_value=0.0, value=def_temp_water, step=1.0)

            st.divider()
            st.subheader("2. Quality Lab Parameters (Optional for New Entry)")

            q_edit_data = None
            if st.session_state["edit_mil_id"] is not None:
                df_q_check = load_data("quality")
                q_match_edit = df_q_check[df_q_check["milling_id"] == st.session_state["edit_mil_id"]]
                if not q_match_edit.empty:
                    q_edit_data = q_match_edit.iloc[0]

            qc1, qc2, qc3 = st.columns(3)
            with qc1:
                def_tdate = datetime.date.today()
                if q_edit_data is not None and pd.notna(q_edit_data["test_date"]):
                    try:
                        def_tdate = datetime.datetime.strptime(q_edit_data["test_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                q_test_date = st.date_input("Lab Test Date", value=def_tdate).strftime("%d %b %Y")

                def_mm = float(q_edit_data["moisture_milled"]) if q_edit_data is not None and pd.notna(q_edit_data["moisture_milled"]) else 0.0
                moisture_milled = st.number_input("Moisture % (Milled/Atta)", min_value=0.0, value=def_mm, step=0.1, format="%.1f")

                def_gran = str(q_edit_data["granulation"]) if q_edit_data is not None and pd.notna(q_edit_data["granulation"]) else ""
                granulation = st.text_input("Granulation / Fineness", value=def_gran, placeholder="e.g. Fine / 95% through 150 mesh")
            with qc2:
                def_ccl4 = str(q_edit_data["ccl4"]) if q_edit_data is not None and pd.notna(q_edit_data["ccl4"]) else ""
                ccl4 = st.text_input("CCL4 Test", value=def_ccl4, placeholder="e.g. Sound / Clean")

                def_ash = float(q_edit_data["ash_aia"]) if q_edit_data is not None and pd.notna(q_edit_data["ash_aia"]) else 0.0
                ash_aia = st.number_input("Ash / AIA %", min_value=0.0, value=def_ash, step=0.01, format="%.2f")

                def_aa = float(q_edit_data["alcoholic_acidity"]) if q_edit_data is not None and pd.notna(q_edit_data["alcoholic_acidity"]) else 0.0
                alcoholic_acidity = st.number_input("Alcoholic Acidity", min_value=0.0, value=def_aa, step=0.01, format="%.2f")
            with qc3:
                def_wap = float(q_edit_data["wap"]) if q_edit_data is not None and "wap" in q_edit_data and pd.notna(q_edit_data["wap"]) else 0.0
                wap = st.number_input("WAP (Water Absorption / Wapsi)", min_value=0.0, value=def_wap, step=0.1, format="%.1f")

                def_gluten = str(q_edit_data["gluten"]) if q_edit_data is not None and pd.notna(q_edit_data["gluten"]) else ""
                gluten = st.text_input("Gluten %", value=def_gluten, placeholder="e.g. 9.5%")

                def_chapati = str(q_edit_data["chapati_sensory"]) if q_edit_data is not None and pd.notna(q_edit_data["chapati_sensory"]) else ""
                chapati_sensory = st.text_input("Chapati Sensory / Quality", value=def_chapati, placeholder="e.g. Soft, Excellent")

            btn_mil_label = "Update Milling & Quality Record" if st.session_state["edit_mil_id"] is not None else "Save Milling & Quality Entry"
            submit_mil_q = st.form_submit_button(label=btn_mil_label)

            if submit_mil_q:
                conn = get_connection()
                cursor = conn.cursor()
                if st.session_state["edit_mil_id"] is not None:
                    m_id = st.session_state["edit_mil_id"]
                    cursor.execute("""
                        UPDATE milling 
                        SET milling_date=?, miller_name=?, milling_qty=?, tempering_time=?, tempering_water=?
                        WHERE id=?
                    """, (milling_date, milling_miller_name, milling_qty, tempering_time, tempering_water, m_id))

                    cursor.execute("SELECT id FROM quality WHERE milling_id = ?", (m_id,))
                    q_exists = cursor.fetchone()
                    if q_exists:
                        cursor.execute("""
                            UPDATE quality 
                            SET test_date=?, miller_name=?, moisture_milled=?, granulation=?, ccl4=?, ash_aia=?, alcoholic_acidity=?, wap=?, gluten=?, chapati_sensory=?
                            WHERE milling_id=?
                        """, (q_test_date, milling_miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory, m_id))
                    else:
                        cursor.execute("""
                            INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (m_id, q_test_date, milling_miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"Milling & Quality Record ID {m_id} Updated Successfully!")
                    st.session_state["edit_mil_id"] = None
                    st.rerun()
                else:
                    cursor.execute("""
                        INSERT INTO milling (milling_date, miller_name, milling_qty, tempering_time, tempering_water)
                        VALUES (?, ?, ?, ?, ?)
                    """, (milling_date, milling_miller_name, milling_qty, tempering_time, tempering_water))
                    new_milling_id = cursor.lastrowid

                    cursor.execute("""
                        INSERT INTO quality (milling_id, test_date, miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_milling_id, q_test_date, milling_miller_name, moisture_milled, granulation, ccl4, ash_aia, alcoholic_acidity, wap, gluten, chapati_sensory))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"Milling & Quality Entry Saved Successfully for {milling_miller_name}!")
                    st.rerun()

    st.subheader("Saved Milling & Quality Records")
    df_m_disp = load_data("milling")
    df_q_disp = load_data("quality")
    if not df_m_disp.empty:
        st.write("### Milling Entries Table")
        st.dataframe(df_m_disp, use_container_width=True)
    if not df_q_disp.empty:
        st.write("### Quality Lab Test Table (with WAP)")
        st.dataframe(df_q_disp, use_container_width=True)

elif menu == "3. Finished Goods & Yield":
    st.header("Finished Goods Production & Yield Tracking")

    if "edit_fg_id" not in st.session_state:
        st.session_state["edit_fg_id"] = None

    df_mil = load_data("milling")
    df_fg_existing = load_data("finished_goods")

    if df_mil.empty:
        st.warning("Pehle Menu 2 se Milling entry karein, tabhi Finished Goods entry ho sakegi.")
    else:
        action_type_fg = st.radio(
            "Action Mode", ["➕ New Finished Goods Entry", "✏️ Edit / 🗑️ Delete Existing Finished Goods"], horizontal=True, key="mode_fg"
        )

        edit_fg_data = None
        if action_type_fg == "✏️ Edit / 🗑️ Delete Existing Finished Goods" and not df_fg_existing.empty:
            df_fg_existing["label"] = (
                "ID: " + df_fg_existing["id"].astype(str) + " | " + df_fg_existing["miller_name"] + " | SKU: " + df_fg_existing["product_code"] + " (" + df_fg_existing["production_date"] + ")"
            )
            sel_fg_mod = st.selectbox("Select Finished Goods Record to Modify/Delete", df_fg_existing["label"].tolist(), key="sel_fg_mod")
            row_edit_fg = df_fg_existing[df_fg_existing["label"] == sel_fg_mod].iloc[0]
            st.session_state["edit_fg_id"] = int(row_edit_fg["id"])
            edit_fg_data = row_edit_fg

            with st.expander("⚠️ Delete Finished Goods Confirmation Box", expanded=False):
                confirm_del_fg = st.checkbox("Haan, main is finished goods record ko delete karna chahta hoon", key="conf_del_fg_rec")
                if st.button("🗑️ Confirm & Delete Finished Goods", type="primary", key="btn_del_fg_rec"):
                    if confirm_del_fg:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM finished_goods WHERE id = ?", (st.session_state["edit_fg_id"],))
                        conn.commit()
                        conn.close()
                        st.success("Finished Goods Record deleted successfully!")
                        st.session_state["edit_fg_id"] = None
                        st.rerun()
                    else:
                        st.error("Pehle confirmation checkbox par tick karein!")
        else:
            if action_type_fg != "✏️ Edit / 🗑️ Delete Existing Finished Goods":
                st.session_state["edit_fg_id"] = None

        if action_type_fg == "➕ New Finished Goods Entry" or st.session_state["edit_fg_id"] is not None:
            if st.session_state["edit_fg_id"] is None and not df_fg_existing.empty and "milling_id" in df_fg_existing.columns:
                completed_milling_ids = df_fg_existing["milling_id"].tolist()
                df_mil_available = df_mil[~df_mil["id"].isin(completed_milling_ids)]
            else:
                df_mil_available = df_mil.copy()

            if st.session_state["edit_fg_id"] is None and df_mil_available.empty:
                st.success("🎉 Sabhi milling batches ki Finished Goods entry ki ja chuki hai!")
            else:
                if st.session_state["edit_fg_id"] is not None:
                    df_mil_available = df_mil.copy()

                df_mil_available["label"] = (
                    "Batch ID: "
                    + df_mil_available["id"].astype(str)
                    + " | "
                    + df_mil_available["miller_name"]
                    + " ("
                    + df_mil_available["milling_date"]
                    + ")"
                )

                default_mil_idx = 0
                if st.session_state["edit_fg_id"] is not None and edit_fg_data is not None:
                    matched_mil = df_mil_available[df_mil_available["id"] == edit_fg_data["milling_id"]]
                    if not matched_mil.empty:
                        matched_label = matched_mil.iloc[0]["label"]
                        if matched_label in df_mil_available["label"].tolist():
                            default_mil_idx = df_mil_available["label"].tolist().index(matched_label)

                sel_milling = st.selectbox(
                    "Select Milling Batch", df_mil_available["label"].tolist(), index=default_mil_idx, key="sel_milling_fg"
                )

                if sel_milling is not None:
                    row_mil = df_mil_available[df_mil_available["label"] == sel_milling].iloc[0]
                    milling_id = int(row_mil["id"])
                    miller_name = row_mil["miller_name"]
                    milling_qty = float(row_mil["milling_qty"])
                    milling_date_str = row_mil["milling_date"]

                    st.info(f"Selected Miller: **{miller_name}** | Milling Date: **{milling_date_str}** | Milling Qty: **{milling_qty:,.2f} kg**")

                    with st.form("fg_form", clear_on_submit=False):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            default_prod_date = datetime.date.today()
                            if edit_fg_data is not None:
                                try:
                                    default_prod_date = datetime.datetime.strptime(edit_fg_data["production_date"], "%d %b %Y").date()
                                except Exception:
                                    pass
                            prod_date_obj = st.date_input("Production Date", value=default_prod_date)
                            production_date = prod_date_obj.strftime("%d %b %Y")
                        with c2:
                            default_mfd = datetime.date.today()
                            if edit_fg_data is not None:
                                try:
                                    default_mfd = datetime.datetime.strptime("01 " + edit_fg_data["mfd_date"], "%d %b %Y").date()
                                except Exception:
                                    pass
                            mfd_date_obj = st.date_input("MFD Date", value=default_mfd)
                            mfd_date = mfd_date_obj.strftime("%b %Y")
                        with c3:
                            default_exp = datetime.date.today() + datetime.timedelta(days=180)
                            if edit_fg_data is not None:
                                try:
                                    default_exp = datetime.datetime.strptime(edit_fg_data["expiry_date"], "%d %b %Y").date()
                                except Exception:
                                    pass
                            expiry_date_obj = st.date_input("Expiry Date", value=default_exp)
                            expiry_date = expiry_date_obj.strftime("%d %b %Y")

                        st.divider()
                        st.subheader("SKU & MRP Configuration")

                        sku_options = ["500g Pouch", "1kg Pouch", "2kg Pouch", "5kg Pouch", "Custom SKU"]
                        default_sku_idx = 0
                        if edit_fg_data is not None:
                            p_code = edit_fg_data["product_code"]
                            if "500g" in p_code: default_sku_idx = 0
                            elif "1kg" in p_code: default_sku_idx = 1
                            elif "2kg" in p_code: default_sku_idx = 2
                            elif "5kg" in p_code: default_sku_idx = 3
                            else: default_sku_idx = 4

                        sc1, sc2, sc3, sc4 = st.columns(4)
                        with sc1:
                            sku_type = st.selectbox("Select SKU Type", sku_options, index=default_sku_idx, key="fg_sku_type")
                        with sc2:
                            default_pcode = edit_fg_data["product_code"] if edit_fg_data is not None else "BN-ATTA-1KG"
                            product_code = st.text_input("Product Code / SKU Name", value=default_pcode)
                        with sc3:
                            default_mrp = float(edit_fg_data["mrp"]) if edit_fg_data is not None and pd.notna(edit_fg_data.get("mrp")) else 0.0
                            mrp = st.number_input("MRP (Rs)", value=default_mrp, step=1.0, format="%.2f")
                        with sc4:
                            default_p_count = 0
                            if edit_fg_data is not None:
                                default_p_count = int(edit_fg_data.get("pouch_1kg", 0) or edit_fg_data.get("pouch_500g", 0) or edit_fg_data.get("pouch_2kg", 0) or edit_fg_data.get("pouch_5kg", 0))
                            pouch_count = st.number_input("Number of Pouches / Units", min_value=0, value=default_p_count, step=1)

                        st.divider()
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            default_bran = float(edit_fg_data["bran_qty"]) if edit_fg_data is not None else 0.0
                            bran_qty = st.number_input("Bran Quantity (kg)", min_value=0.0, value=default_bran, step=1.0, format="%.2f")
                        with rc2:
                            default_refr = float(edit_fg_data["refraction_qty"]) if edit_fg_data is not None else 0.0
                            refraction_qty = st.number_input("Refraction Quantity (kg)", min_value=0.0, value=default_refr, step=1.0, format="%.2f")

                        btn_label_fg = "Update Finished Goods" if st.session_state["edit_fg_id"] is not None else "Calculate Yield & Save Finished Goods"
                        submit_fg = st.form_submit_button(label=btn_label_fg)

                        if submit_fg:
                            f_mrp = float(mrp) if mrp is not None else 0.0
                            f_bran = float(bran_qty) if bran_qty is not None else 0.0
                            f_refr = float(refraction_qty) if refraction_qty is not None else 0.0
                            f_count = int(pouch_count) if pouch_count is not None else 0

                            multiplier = 1.0
                            if "500g" in sku_type: multiplier = 0.5
                            elif "1kg" in sku_type: multiplier = 1.0
                            elif "2kg" in sku_type: multiplier = 2.0
                            elif "5kg" in sku_type: multiplier = 5.0

                            total_finished_qty = f_count * multiplier

                            bran_pct = (f_bran / milling_qty) * 100 if milling_qty > 0 else 0.0
                            refraction_pct = (f_refr / milling_qty) * 100 if milling_qty > 0 else 0.0
                            yield_pct = (total_finished_qty / milling_qty) * 100 if milling_qty > 0 else 0.0

                            total_accounted = total_finished_qty + f_bran + f_refr
                            processing_loss_qty = milling_qty - total_accounted
                            processing_loss_pct = (processing_loss_qty / milling_qty) * 100 if milling_qty > 0 else 0.0

                            conn = get_connection()
                            cursor = conn.cursor()

                            if st.session_state["edit_fg_id"] is not None:
                                cursor.execute("""
                                    UPDATE finished_goods 
                                    SET milling_id=?, production_date=?, miller_name=?, mfd_date=?, expiry_date=?, mrp=?, product_code=?, pouch_500g=?, pouch_1kg=?, pouch_2kg=?, pouch_5kg=?, total_finished_qty=?, bran_qty=?, bran_pct=?, refraction_qty=?, refraction_pct=?, yield_pct=?, processing_loss_pct=?
                                    WHERE id=?
                                """, (
                                    milling_id, production_date, miller_name, mfd_date, expiry_date, f_mrp, product_code,
                                    f_count if "500g" in sku_type else 0,
                                    f_count if "1kg" in sku_type else 0,
                                    f_count if "2kg" in sku_type else 0,
                                    f_count if "5kg" in sku_type else 0,
                                    round(total_finished_qty, 2), f_bran, f"{bran_pct:.2f}%", f_refr, f"{refraction_pct:.2f}%", f"{yield_pct:.2f}%", f"{processing_loss_pct:.2f}%",
                                    st.session_state["edit_fg_id"]
                                ))
                                conn.commit()
                                conn.close()
                                st.success("Finished Goods Updated Successfully!")
                                st.session_state["edit_fg_id"] = None
                                st.rerun()
                            else:
                                cursor.execute("""
                                    INSERT INTO finished_goods (milling_id, production_date, miller_name, mfd_date, expiry_date, mrp, product_code, pouch_500g, pouch_1kg, pouch_2kg, pouch_5kg, total_finished_qty, bran_qty, bran_pct, refraction_qty, refraction_pct, yield_pct, processing_loss_pct)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    milling_id, production_date, miller_name, mfd_date, expiry_date, f_mrp, product_code,
                                    f_count if "500g" in sku_type else 0,
                                    f_count if "1kg" in sku_type else 0,
                                    f_count if "2kg" in sku_type else 0,
                                    f_count if "5kg" in sku_type else 0,
                                    round(total_finished_qty, 2), f_bran, f"{bran_pct:.2f}%", f_refr, f"{refraction_pct:.2f}%", f"{yield_pct:.2f}%", f"{processing_loss_pct:.2f}%"
                                ))
                                conn.commit()
                                conn.close()
                                st.success("Finished Goods Saved Successfully!")
                                st.rerun()

    st.subheader("Saved Finished Goods Records")
    df_fg_show = load_data("finished_goods")
    if not df_fg_show.empty:
        st.dataframe(df_fg_show, use_container_width=True)

elif menu == "4. Better Nutrition Packing Material":
    st.header("Packing Material Management")
    
    if "edit_pm_id" not in st.session_state:
        st.session_state["edit_pm_id"] = None

    df_pm_saved = load_data("packing_material")
    action_type_pm = "➕ New Packing Entry"
    if not df_pm_saved.empty:
        action_type_pm = st.radio("Action Mode", ["➕ New Packing Entry", "✏️ Edit / 🗑️ Delete Existing Packing"], horizontal=True, key="mode_pm")

    edit_pm_data = None
    if action_type_pm == "✏️ Edit / 🗑️ Delete Existing Packing" and not df_pm_saved.empty:
        df_pm_saved["label"] = "ID: " + df_pm_saved["id"].astype(str) + " | Date: " + df_pm_saved["date"] + " | Miller: " + df_pm_saved["miller_name"]
        sel_pm_mod = st.selectbox("Select Record to Modify/Delete", df_pm_saved["label"].tolist(), key="sel_pm_mod")
        row_edit_pm = df_pm_saved[df_pm_saved["label"] == sel_pm_mod].iloc[0]
        st.session_state["edit_pm_id"] = int(row_edit_pm["id"])
        edit_pm_data = row_edit_pm

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del_pm = st.checkbox("Haan, main is packing material record ko delete karna chahta hoon", key="conf_del_pm")
            if st.button("🗑️ Confirm & Delete Packing Record", type="primary", key="btn_del_pm_rec"):
                if confirm_del_pm:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM packing_material WHERE id = ?", (st.session_state["edit_pm_id"],))
                    conn.commit()
                    conn.close()
                    st.success("Packing Material Record deleted successfully!")
                    st.session_state["edit_pm_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        st.session_state["edit_pm_id"] = None

    if action_type_pm == "➕ New Packing Entry" or st.session_state["edit_pm_id"] is not None:
        def_pm_miller = edit_pm_data["miller_name"] if edit_pm_data is not None else None
        pm_miller_name = get_miller_input("pm", def_pm_miller)

        with st.form("pm_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                default_pm_date = datetime.date.today()
                if edit_pm_data is not None:
                    try:
                        default_pm_date = datetime.datetime.strptime(edit_pm_data["date"], "%d %b %Y").date()
                    except Exception:
                        pass
                pm_date_obj = st.date_input("Entry Date", value=default_pm_date)
                pm_date_str = pm_date_obj.strftime("%d %b %Y")

                carton_opts = ["Master Carton (1kg)", "Master Carton (500g)", "Master Carton (2kg)", "Master Carton (5kg)", "Other"]
                default_carton_idx = 0
                if edit_pm_data is not None and edit_pm_data["carton_type"] in carton_opts:
                    default_carton_idx = carton_opts.index(edit_pm_data["carton_type"])
                carton_type = st.selectbox("Carton Type", carton_opts, index=default_carton_idx)

            with c2:
                default_cartons = int(edit_pm_data["cartons_sent"]) if edit_pm_data is not None and pd.notna(edit_pm_data["cartons_sent"]) else 0
                cartons_sent = st.number_input("Cartons Sent / Used", min_value=0, value=default_cartons, step=1)

                default_tape = int(edit_pm_data["tape_sent"]) if edit_pm_data is not None and pd.notna(edit_pm_data["tape_sent"]) else 0
                tape_sent = st.number_input("Tape Rolls Sent", min_value=0, value=default_tape, step=1)

            with c3:
                default_oxysorb = int(edit_pm_data["oxysorb_qty"]) if edit_pm_data is not None and pd.notna(edit_pm_data["oxysorb_qty"]) else 0
                oxysorb_qty = st.number_input("Oxysorb Packets Qty", min_value=0, value=default_oxysorb, step=1)

                roll_opts = ["1kg Roll", "500g Roll", "2kg Roll", "5kg Roll", "None"]
                default_roll_idx = 0
                if edit_pm_data is not None and edit_pm_data["roll_sku"] in roll_opts:
                    default_roll_idx = roll_opts.index(edit_pm_data["roll_sku"])
                roll_sku = st.selectbox("Roll SKU", roll_opts, index=default_roll_idx)

            default_roll_qty = float(edit_pm_data["roll_qty_sent"]) if edit_pm_data is not None and pd.notna(edit_pm_data["roll_qty_sent"]) else 0.0
            roll_qty_sent = st.number_input("Roll Quantity Sent (kg/meters)", min_value=0.0, value=default_roll_qty, step=1.0, format="%.2f")

            btn_pm_label = "Update Packing Material Record" if st.session_state["edit_pm_id"] is not None else "Save Packing Material Entry"
            submit_pm = st.form_submit_button(label=btn_pm_label)

            if submit_pm:
                conn = get_connection()
                cursor = conn.cursor()
                if st.session_state["edit_pm_id"] is not None:
                    cursor.execute("""
                        UPDATE packing_material 
                        SET date=?, miller_name=?, carton_type=?, cartons_sent=?, tape_sent=?, oxysorb_qty=?, roll_sku=?, roll_qty_sent=?
                        WHERE id=?
                    """, (pm_date_str, pm_miller_name, carton_type, cartons_sent, tape_sent, oxysorb_qty, roll_sku, roll_qty_sent, st.session_state["edit_pm_id"]))
                    conn.commit()
                    conn.close()
                    st.success("Packing Material Updated Successfully!")
                    st.session_state["edit_pm_id"] = None
                    st.rerun()
                else:
                    cursor.execute("""
                        INSERT INTO packing_material (date, miller_name, carton_type, cartons_sent, tape_sent, oxysorb_qty, roll_sku, roll_qty_sent)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (pm_date_str, pm_miller_name, carton_type, cartons_sent, tape_sent, oxysorb_qty, roll_sku, roll_qty_sent))
                    conn.commit()
                    conn.close()
                    st.success("Packing Material Saved Successfully!")
                    st.rerun()

    st.subheader("Existing Packing Material Records")
    df_pm_show = load_data("packing_material")
    if not df_pm_show.empty:
        st.dataframe(df_pm_show, use_container_width=True)

elif menu == "5. Daily Dispatch Entry":
    st.header("Daily Dispatch Management")
    
    if "edit_disp_id" not in st.session_state:
        st.session_state["edit_disp_id"] = None

    df_disp_saved = load_data("dispatch")
    action_type_disp = "➕ New Dispatch Entry"
    if not df_disp_saved.empty:
        action_type_disp = st.radio("Action Mode", ["➕ New Dispatch Entry", "✏️ Edit / 🗑️ Delete Existing Dispatch"], horizontal=True, key="mode_disp")

    edit_disp_data = None
    if action_type_disp == "✏️ Edit / 🗑️ Delete Existing Dispatch" and not df_disp_saved.empty:
        df_disp_saved["label"] = "ID: " + df_disp_saved["id"].astype(str) + " | Date: " + df_disp_saved["dispatch_date"] + " | Vehicle: " + df_disp_saved["vehicle_no"]
        sel_disp_mod = st.selectbox("Select Dispatch Record to Modify/Delete", df_disp_saved["label"].tolist(), key="sel_disp_mod")
        row_edit_disp = df_disp_saved[df_disp_saved["label"] == sel_disp_mod].iloc[0]
        st.session_state["edit_disp_id"] = int(row_edit_disp["id"])
        edit_disp_data = row_edit_disp

        with st.expander("⚠️ Delete Confirmation Box", expanded=False):
            confirm_del_disp = st.checkbox("Haan, main is dispatch record ko delete karna chahta hoon", key="conf_del_disp")
            if st.button("🗑️ Confirm & Delete Dispatch Record", type="primary", key="btn_del_disp_rec"):
                if confirm_del_disp:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM dispatch WHERE id = ?", (st.session_state["edit_disp_id"],))
                    conn.commit()
                    conn.close()
                    st.success("Dispatch Record deleted successfully!")
                    st.session_state["edit_disp_id"] = None
                    st.rerun()
                else:
                    st.error("Pehle confirmation checkbox par tick karein!")
    else:
        st.session_state["edit_disp_id"] = None

    if action_type_disp == "➕ New Dispatch Entry" or st.session_state["edit_disp_id"] is not None:
        def_disp_miller = edit_disp_data["miller_name"] if edit_disp_data is not None else None
        disp_miller_name = get_miller_input("disp", def_disp_miller)

        with st.form("dispatch_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                default_disp_date = datetime.date.today()
                if edit_disp_data is not None:
                    try:
                        default_disp_date = datetime.datetime.strptime(edit_disp_data["dispatch_date"], "%d %b %Y").date()
                    except Exception:
                        pass
                disp_date_obj = st.date_input("Dispatch Date", value=default_disp_date)
                dispatch_date_str = disp_date_obj.strftime("%d %b %Y")

                default_veh_no = edit_disp_data["vehicle_no"] if edit_disp_data is not None else ""
                vehicle_no = st.text_input("Vehicle Number", value=default_veh_no, placeholder="e.g. UP-75-BT-1234")

            with c2:
                default_cartons_used = int(edit_disp_data["cartons_used"]) if edit_disp_data is not None and pd.notna(edit_disp_data["cartons_used"]) else 0
                cartons_used = st.number_input("Cartons Used", min_value=0, value=default_cartons_used, step=1)

            st.divider()
            st.subheader("Dispatched Quantities (Pouches)")
            dc1, dc2, dc3, dc4 = st.columns(4)
            with dc1:
                def_d500 = int(edit_disp_data["disp_500g"]) if edit_disp_data is not None and pd.notna(edit_disp_data.get("disp_500g")) else 0
                disp_500g = st.number_input("500g Pouches", min_value=0, value=def_d500, step=1)
            with dc2:
                def_d1k = int(edit_disp_data["disp_1kg"]) if edit_disp_data is not None and pd.notna(edit_disp_data.get("disp_1kg")) else 0
                disp_1kg = st.number_input("1kg Pouches", min_value=0, value=def_d1k, step=1)
            with dc3:
                def_d2k = int(edit_disp_data["disp_2kg"]) if edit_disp_data is not None and pd.notna(edit_disp_data.get("disp_2kg")) else 0
                disp_2kg = st.number_input("2kg Pouches", min_value=0, value=def_d2k, step=1)
            with dc4:
                def_d5k = int(edit_disp_data["disp_5kg"]) if edit_disp_data is not None and pd.notna(edit_disp_data.get("disp_5kg")) else 0
                disp_5kg = st.number_input("5kg Pouches", min_value=0, value=def_d5k, step=1)

            default_rem_disp = edit_disp_data["remarks"] if edit_disp_data is not None and pd.notna(edit_disp_data.get("remarks")) else ""
            remarks_disp = st.text_input("Dispatch Remarks / Party Name", value=default_rem_disp)

            btn_disp_label = "Update Dispatch Record" if st.session_state["edit_disp_id"] is not None else "Save Dispatch Entry"
            submit_disp = st.form_submit_button(label=btn_disp_label)

            if submit_disp:
                total_dispatched_wt = (disp_500g * 0.5) + (disp_1kg * 1.0) + (disp_2kg * 2.0) + (disp_5kg * 5.0)

                conn = get_connection()
                cursor = conn.cursor()
                if st.session_state["edit_disp_id"] is not None:
                    cursor.execute("""
                        UPDATE dispatch 
                        SET dispatch_date=?, miller_name=?, vehicle_no=?, disp_500g=?, disp_1kg=?, disp_2kg=?, disp_5kg=?, total_dispatched_wt=?, cartons_used=?, remarks=?
                        WHERE id=?
                    """, (dispatch_date_str, disp_miller_name, vehicle_no, disp_500g, disp_1kg, disp_2kg, disp_5kg, round(total_dispatched_wt, 2), cartons_used, remarks_disp, st.session_state["edit_disp_id"]))
                    conn.commit()
                    conn.close()
                    st.success("Dispatch Record Updated Successfully!")
                    st.session_state["edit_disp_id"] = None
                    st.rerun()
                else:
                    cursor.execute("""
                        INSERT INTO dispatch (dispatch_date, miller_name, vehicle_no, disp_500g, disp_1kg, disp_2kg, disp_5kg, total_dispatched_wt, cartons_used, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (dispatch_date_str, disp_miller_name, vehicle_no, disp_500g, disp_1kg, disp_2kg, disp_5kg, round(total_dispatched_wt, 2), cartons_used, remarks_disp))
                    conn.commit()
                    conn.close()
                    st.success(f"Dispatch Saved Successfully! Total Weight: {total_dispatched_wt:,.2f} kg")
                    st.rerun()

    st.subheader("Existing Dispatch Records")
    df_disp_show = load_data("dispatch")
    if not df_disp_show.empty:
        st.dataframe(df_disp_show, use_container_width=True)

elif menu == "6. Master Records & Export (Admin Controls)":
    st.header("Master Records & Data Export (Admin Only)")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Raw Material", "Milling", "Quality Lab", "Finished Goods", "Packing Material", "Dispatch"
    ])
    
    with tab1:
        st.subheader("Raw Material Master Table")
        df_m1 = load_data("raw_material")
        st.dataframe(df_m1, use_container_width=True)
    with tab2:
        st.subheader("Milling Master Table")
        df_m2 = load_data("milling")
        st.dataframe(df_m2, use_container_width=True)
    with tab3:
        st.subheader("Quality Lab Master Table (with WAP)")
        df_m3 = load_data("quality")
        st.dataframe(df_m3, use_container_width=True)
    with tab4:
        st.subheader("Finished Goods Master Table")
        df_m4 = load_data("finished_goods")
        st.dataframe(df_m4, use_container_width=True)
    with tab5:
        st.subheader("Packing Material Master Table")
        df_m5 = load_data("packing_material")
        st.dataframe(df_m5, use_container_width=True)
    with tab6:
        st.subheader("Dispatch Master Table")
        df_m6 = load_data("dispatch")
        st.dataframe(df_m6, use_container_width=True)
