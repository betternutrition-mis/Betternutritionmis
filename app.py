import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# Page configuration
st.set_page_config(page_title="Better Nutrition MIS", layout="wide")
st.title("Better Nutrition MIS - Complete Dashboard")

# Supabase Connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Raw Material", "Milling", "Finished Goods", "Master Records"])

# --- TAB 1: Raw Material ---
with tab1:
    st.subheader("Raw Material Entry")
    with st.form("raw_material_form"):
        c1, c2 = st.columns(2)
        with c1:
            vendor = st.text_input("Vendor Name *")
            mat = st.text_input("Material Name *")
        with c2:
            qty = st.number_input("Gross Qty *", value=0.0)
            bags = st.number_input("Total Bags *", value=0)
        
        if st.form_submit_button("Save RM"):
            data = {"vendor_name": vendor, "material_name": mat, "gross_qty": qty, "total_bags": bags}
            supabase.table("raw_material").insert(data).execute()
            st.success("Saved!")

# --- TAB 2: Milling ---
with tab2:
    st.subheader("Milling Entry")
    with st.form("milling_form"):
        miller = st.text_input("Miller Name")
        out_qty = st.number_input("Output Qty")
        if st.form_submit_button("Save Milling"):
            data = {"miller_name": miller, "output_qty": out_qty}
            supabase.table("milling").insert(data).execute()
            st.success("Milling Saved!")

# --- TAB 3: Finished Goods ---
with tab3:
    st.subheader("Finished Goods Entry")
    with st.form("fg_form"):
        product = st.text_input("Product Name")
        fg_qty = st.number_input("FG Qty")
        if st.form_submit_button("Save FG"):
            data = {"product_name": product, "fg_qty": fg_qty}
            supabase.table("finished_goods").insert(data).execute()
            st.success("FG Saved!")

# --- TAB 4: Master Records (Combined View) ---
with tab4:
    st.subheader("Master Sheet - Records")
    try:
        # Example: Fetching Raw Material for Master Sheet
        rm_data = supabase.table("raw_material").select("*").execute()
        st.write("Raw Material Table:", pd.DataFrame(rm_data.data))
        
        # Add similar logic for Milling/FG if needed
    except Exception as e:
        st.error(f"Error loading records: {e}")
