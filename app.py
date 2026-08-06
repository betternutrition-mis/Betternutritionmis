import streamlit as st
import sqlite3
import datetime
import pandas as pd
import os

# Database Connection
def get_connection():
    db_path = os.path.join(os.getcwd(), "database.db")
    return sqlite3.connect(db_path, check_same_thread=False)

def load_data(table_name):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

# Create Tables
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # 1. Raw Material Receiving
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT,
            date TEXT,
            item_name TEXT,
            qty REAL
        )
    """)
    # 2. Milling Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milling (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            miller_name TEXT,
            milling_date TEXT,
            milling_qty REAL
        )
    """)
    # 3. Finished Goods
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finished_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milling_id INTEGER,
            production_date TEXT,
            miller_name TEXT,
            product_code TEXT,
            total_finished_qty REAL,
            bran_qty REAL,
            refraction_qty REAL,
            yield_pct TEXT,
            processing_loss_pct TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", [
    "1. Dashboard", 
    "2. Raw Material Receiving", 
    "3. Milling Entry", 
    "4. Finished Goods", 
    "5. Master Sheet"
])

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "1. Dashboard":
    st.header("Dashboard")
    # Add your metric logic here...

# ==========================================
# 2. RAW MATERIAL RECEIVING
# ==========================================
elif menu == "2. Raw Material Receiving":
    st.header("Raw Material Receiving")
    with st.form("rm_form"):
        supplier = st.text_input("Supplier Name")
        date = st.date_input("Date")
        item = st.text_input("Item Name")
        qty = st.number_input("Quantity (kg)", min_value=0.0)
        if st.form_submit_button("Save RM"):
            conn = get_connection()
            conn.execute("INSERT INTO raw_material (supplier_name, date, item_name, qty) VALUES (?,?,?,?)",
                         (supplier, str(date), item, qty))
            conn.commit()
            conn.close()
            st.success("Saved!")

# ==========================================
# 3. MILLING ENTRY
# ==========================================
elif menu == "3. Milling Entry":
    st.header("Milling Entry")
    # (Aapka existing milling logic yahan rahega)

# ==========================================
# 4. FINISHED GOODS
# ==========================================
elif menu == "4. Finished Goods":
    st.header("Finished Goods Production")
    # (Aapka existing FG logic yahan rahega)

# ==========================================
# 5. MASTER SHEET
# ==========================================
elif menu == "5. Master Sheet":
    st.header("Master Data Sheet")
    
    st.subheader("Raw Material Data")
    st.dataframe(load_data("raw_material"))
    
    st.subheader("Milling Data")
    st.dataframe(load_data("milling"))
    
    st.subheader("Finished Goods Data")
    st.dataframe(load_data("finished_goods"))
    
    # Download button for Excel
    if st.button("Download Master Sheet as CSV"):
        # Logic to merge and download
        st.info("Download feature ready.")
