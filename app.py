import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="Better Nutrition MIS", layout="wide")

def get_connection():
    return sqlite3.connect("flour_mill_erp.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatch (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            dispatch_date TEXT, 
            miller_name TEXT, 
            party_name TEXT, 
            vehicle_number TEXT, 
            bags_30kg INTEGER, 
            bags_10kg INTEGER, 
            pouches_5kg INTEGER, 
            other_qty REAL, 
            total_dispatched_wt REAL, 
            remarks TEXT, 
            entered_by TEXT
        )
    """)
    for col in [
        "party_name TEXT", 
        "vehicle_number TEXT", 
        "bags_30kg INTEGER", 
        "bags_10kg INTEGER", 
        "pouches_5kg INTEGER", 
        "other_qty REAL",
        "total_dispatched_wt REAL",
        "remarks TEXT",
        "entered_by TEXT"
    ]:
        try:
            cursor.execute(f"ALTER TABLE dispatch ADD COLUMN {col}")
        except Exception:
            pass
    conn.commit()
    conn.close()

init_db()

st.sidebar.title("Navigation Menu")
menu_option = st.sidebar.selectbox(
    "Select Option", 
    [
        "1. Raw Material Received", 
        "2. Milling & Quality Lab Entry", 
        "3. Finished Goods & Yield", 
        "4. Better Nutrition Packing Material", 
        "5. Daily Dispatch Entry", 
        "6. Master Records & Export (Admin)"
    ]
)

# 5. Daily Dispatch Entry Section
if menu_option == "5. Daily Dispatch Entry":
    st.title("📦 Daily Dispatch Entry & Management")
    st.write("Log outgoing stock dispatches SKU-wise with automatic total weight calculation.")

    BASE_MILLER_LIST = [
        "Shree Balram Agro",
        "IKON ORG.",
        "Sathvik Agro",
        "Satya Naraian Kesho",
        "Tara Grains",
        "Other"
    ]

    selected_option = st.selectbox("Miller Location / Name", BASE_MILLER_LIST)
    miller_name = selected_option
    if selected_option == "Other":
        custom_name = st.text_input("Enter New Miller Name Here")
        if custom_name:
            miller_name = custom_name

    with st.form("dispatch_form"):
        c1, c2 = st.columns(2)
        with c1:
            disp_date_obj = st.date_input("Dispatch Date", datetime.date.today())
            dispatch_date = disp_date_obj.strftime("%d %b %Y")
            
            party_name = st.text_input("Party Name / Customer Name")
            vehicle_no = st.text_input("Vehicle Number", placeholder="e.g. UP-75-XYZ-1234")
        with c2:
            st.write("**SKU-wise Number of Pouches / Bags**")
            sc1, sc2 = st.columns(2)
            with sc1:
                bags_30kg = st.number_input("30 kg Bags", min_value=0, step=1, value=0)
                bags_10kg = st.number_input("10 kg Bags", min_value=0, step=1, value=0)
            with sc2:
                pouches_5kg = st.number_input("5 kg Pouches", min_value=0, step=1, value=0)
                other_qty = st.number_input("Other / Loose Qty (kg)", min_value=0.0, step=1.0, value=0.0)

        auto_total_wt = (bags_30kg * 30.0) + (bags_10kg * 10.0) + (pouches_5kg * 5.0) + other_qty
        st.info(f"📦 **Auto-Calculated Total Dispatched Weight:** {auto_total_wt:,.2f} kg")

        remarks = st.text_input("Dispatch Remarks")
        submit_disp = st.form_submit_button("Save Dispatch Entry")

        if submit_disp:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dispatch (dispatch_date, miller_name, party_name, vehicle_number, bags_30kg, bags_10kg, pouches_5kg, other_qty, total_dispatched_wt, remarks, entered_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dispatch_date, miller_name, party_name, vehicle_no, bags_30kg, bags_10kg, pouches_5kg, other_qty, round(auto_total_wt, 2), remarks, "Rishabh Admin"))
            
            conn.commit()
            conn.close()
            st.success(f"Dispatch Entry Successfully Saved! Total Wt: {auto_total_wt:,.2f} kg.")

    st.subheader("Saved Dispatch Entries")
    conn = get_connection()
    try:
        df_disp_saved = pd.read_sql("SELECT * FROM dispatch", conn)
        if not df_disp_saved.empty:
            st.dataframe(df_disp_saved, use_container_width=True)
        else:
            st.info("No dispatch records found yet.")
    except Exception:
        st.info("No dispatch records found yet.")
    conn.close()

# Baaki sabhi options ke liye aapka Dashboard / Master Records View wapas laa diya hai
else:
    st.title("📊 Better Nutrition - Dashboard & Master Records")
    st.write(f"Displaying: **{menu_option}**")
    
    conn = get_connection()
    try:
        if "Raw Material" in menu_option:
            df = pd.read_sql("SELECT * FROM raw_material", conn)
        elif "Milling" in menu_option:
            df = pd.read_sql("SELECT * FROM milling_quality", conn)
        elif "Finished Goods" in menu_option:
            df = pd.read_sql("SELECT * FROM finished_goods", conn)
        elif "Packing Material" in menu_option:
            df = pd.read_sql("SELECT * FROM packing_material", conn)
        else:
            # Master Records & Export default view (Sabhi tables ke tabs ya data)
            st.subheader("All System Master Records & Export Data")
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Raw Material", "Milling & Quality", "Finished Goods", "Packing Material", "Dispatch"])
            
            with tab1:
                st.dataframe(pd.read_sql("SELECT * FROM raw_material", conn), use_container_width=True)
            with tab2:
                try: st.dataframe(pd.read_sql("SELECT * FROM milling_quality", conn), use_container_width=True)
                except: st.info("No data")
            with tab3:
                try: st.dataframe(pd.read_sql("SELECT * FROM finished_goods", conn), use_container_width=True)
                except: st.info("No data")
            with tab4:
                try: st.dataframe(pd.read_sql("SELECT * FROM packing_material", conn), use_container_width=True)
                except: st.info("No data")
            with tab5:
                try: st.dataframe(pd.read_sql("SELECT * FROM dispatch", conn), use_container_width=True)
                except: st.info("No data")
            df = None

        if df is not None and not df.empty and menu_option != "6. Master Records & Export (Admin)":
            st.dataframe(df, use_container_width=True)
            
    except Exception as e:
        st.info("Data table is being populated or initialized.")
    
    conn.close()
