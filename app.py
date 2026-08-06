import streamlit as st
import sqlite3
import datetime
import pandas as pd

# Database Connection
def get_connection():
    return sqlite3.connect("database.db", check_same_thread=False)

def load_data(table_name):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

# Create Tables if not exist
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milling (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            miller_name TEXT,
            milling_date TEXT,
            milling_qty REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finished_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milling_id INTEGER,
            production_date TEXT,
            miller_name TEXT,
            mfd_date TEXT,
            expiry_date TEXT,
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
    conn.commit()
    conn.close()

init_db()

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.selectbox("Go to", ["1. Dashboard", "2. Milling Entry", "3. Finished Goods & Yield"])

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu == "1. Dashboard":
    st.header("Dashboard & Overview")
    df_mil = load_data("milling")
    df_fg = load_data("finished_goods")
    
    st.metric("Total Milling Records", len(df_mil))
    st.metric("Total Finished Goods Records", len(df_fg))
    
    st.subheader("Recent Milling Records")
    st.dataframe(df_mil, use_container_width=True)

# ==========================================
# 2. MILLING ENTRY
# ==========================================
elif menu == "2. Milling Entry":
    st.header("Milling Entry Management")
    
    with st.form("milling_form"):
        miller_name = st.text_input("Miller Name")
        milling_date_obj = st.date_input("Milling Date", value=datetime.date.today())
        milling_qty = st.number_input("Milling Quantity (kg)", min_value=0.0, step=1.0)
        
        submitted = st.form_submit_button("Save Milling Entry")
        if submitted:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO milling (miller_name, milling_date, milling_qty) VALUES (?, ?, ?)",
                (miller_name, milling_date_obj.strftime("%d %b %Y"), milling_qty)
            )
            conn.commit()
            conn.close()
            st.success("Milling Entry Saved!")
            st.rerun()

    st.subheader("Existing Milling Batches")
    st.dataframe(load_data("milling"), use_container_width=True)

# ==========================================
# 3. FINISHED GOODS & YIELD
# ==========================================
elif menu == "3. Finished Goods & Yield":
    st.header("Finished Goods Production & Yield Tracking")

    df_mil = load_data("milling")
    
    if df_mil.empty:
        st.warning("Pehle Milling entry karein.")
    else:
        df_mil["label"] = df_mil["id"].astype(str) + " | " + df_mil["miller_name"] + " (" + df_mil["milling_date"] + ")"
        sel_milling = st.selectbox("Select Milling Batch", df_mil["label"].tolist())
        row_mil = df_mil[df_mil["label"] == sel_milling].iloc[0]
        
        milling_id = int(row_mil["id"])
        miller_name = row_mil["miller_name"]
        milling_qty = float(row_mil["milling_qty"])

        with st.form("fg_form"):
            c1, c2, c3 = st.columns(3)
            with c1: production_date = st.date_input("Production Date").strftime("%d %b %Y")
            with c2: mfd_date = st.date_input("MFD Date").strftime("%b %Y")
            with c3: expiry_date = st.date_input("Expiry Date").strftime("%d %b %Y")
            
            product_code = st.text_input("Product Code", "BN-ATTA-1KG")
            c4, c5, c6, c7 = st.columns(4)
            with c4: p500 = st.number_input("500g Pouch", 0)
            with c5: p1kg = st.number_input("1kg Pouch", 0)
            with c6: p2kg = st.number_input("2kg Pouch", 0)
            with c7: p5kg = st.number_input("5kg Pouch", 0)
            
            bran_qty = st.number_input("Bran Qty (kg)", 0.0)
            refraction_qty = st.number_input("Refraction Qty (kg)", 0.0)
            
            submit_fg = st.form_submit_button("Calculate Yield & Save")
            
            if submit_fg:
                total_fg = (p500*0.5) + (p1kg*1.0) + (p2kg*2.0) + (p5kg*5.0)
                bran_pct = (bran_qty / milling_qty) * 100
                ref_pct = (refraction_qty / milling_qty) * 100
                yield_pct = (total_fg / milling_qty) * 100
                loss_pct = 100 - (yield_pct + bran_pct + ref_pct)

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO finished_goods (milling_id, production_date, miller_name, mfd_date, expiry_date, product_code, 
                    pouch_500g, pouch_1kg, pouch_2kg, pouch_5kg, total_finished_qty, bran_qty, bran_pct, 
                    refraction_qty, refraction_pct, yield_pct, processing_loss_pct) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (milling_id, production_date, miller_name, mfd_date, expiry_date, product_code, 
                      p500, p1kg, p2kg, p5kg, total_fg, bran_qty, f"{bran_pct:.2f}%", 
                      refraction_qty, f"{ref_pct:.2f}%", f"{yield_pct:.2f}%", f"{loss_pct:.2f}%"))
                conn.commit()
                conn.close()
                st.success("Finished Goods Saved!")
                st.rerun()

    st.subheader("Saved Records")
    st.dataframe(load_data("finished_goods"), use_container_width=True)
