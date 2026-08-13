import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Better Nutrition ERP", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- HELPER FUNCTIONS ---
def load_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

def get_miller_input(key_prefix, default_val=None):
    df_emp = load_data("employees")
    millers_list = df_emp["employee_name"].tolist() if not df_emp.empty else ["Default Miller"]
    idx = millers_list.index(default_val) if default_val in millers_list else 0
    return st.selectbox("Miller Name", millers_list, index=idx, key=f"miller_sel_{key_prefix}")

# --- STYLING ---
st.markdown("""
    <style>
    .hero-banner { background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN LOGIC ---
if "logged_in" not in st.session_state: st.session_state.update({"logged_in": False, "user_name": "", "user_role": ""})

if not st.session_state["logged_in"]:
    st.markdown('<div class="hero-banner" style="text-align: center;"><h1>🌾 Better Nutrition ERP</h1><p>Please log in</p></div>', unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Employee Name")
        pin = st.text_input("PIN", type="password")
        if st.form_submit_button("Login"):
            df_emp = load_data("employees")
            user = df_emp[(df_emp["employee_name"] == username.strip()) & (df_emp["pin"] == pin.strip())]
            if not user.empty:
                st.session_state.update({"logged_in": True, "user_name": username, "user_role": user.iloc[0]["role"]})
                st.rerun()
            else: st.error("Invalid Credentials!")
    st.stop()

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation Menu", ["1. Raw Material Receiving", "2. Raw Material Quality Lab", "3. Milling Entry", "4. Finished Goods Entry", "5. Dashboards & Stock Ledger"])

# --- CORE LOGIC EXAMPLE (Raw Material Section) ---
if menu == "1. Raw Material Receiving":
    st.subheader("Incoming Raw Material Entry")
    with st.form("rm_form"):
        miller = get_miller_input("rm")
        vendor = st.text_input("Vendor Name")
        qty = st.number_input("Gross Qty")
        # ... बाकी के fields यहाँ जोड़ें ...
        if st.form_submit_button("Save"):
            data = {"vendor_name": vendor, "gross_qty": qty, "miller_name": miller, "entered_by": st.session_state["user_name"]}
            supabase.table("raw_material").insert(data).execute()
            st.success("Saved!")
    st.dataframe(load_data("raw_material"))
