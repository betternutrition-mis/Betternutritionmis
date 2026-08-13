import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import datetime

# Page configuration
st.set_page_config(page_config_title="Better Nutrition MIS", layout="wide")

st.title("Better Nutrition MIS - Supabase Connected")

# Database connection details using SQLAlchemy and Streamlit Secrets
@st.cache_resource
def get_engine():
    db_url = st.secrets["DATABASE_URL"]
    return create_engine(db_url)

try:
    engine = get_engine()
    st.success("Database connection successful!")
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# Session state simulation for current logged user (Agar aapke paas login system hai toh uske hisaab se adjust kar sakte hain)
if "current_logged_user" not in st.session_state:
    st.session_state["current_logged_user"] = "Admin"

current_logged_user = st.session_state["current_logged_user"]

# Helper function for miller input if needed
def get_miller_input(key_prefix, default_val=None):
    return st.text_input("Miller Name", value=default_val or "", key=key_prefix)

# --- 1. Raw Material Form Section ---
st.subheader("Raw Material Entry")
with st.form("raw_material_form"):
    rc1, rc2, rc3 = st.columns(3)
    
    with rc1:
        entry_date_obj = st.date_input("Date", value=datetime.date.today())
        entry_date = entry_date_obj.strftime("%d %b %Y")
        vendor_name = st.text_input("Vendor Name *", placeholder="Type...")
        material_name = st.text_input("Material Name *", placeholder="Type...")
        
    with rc2:
        miller_name = get_miller_input("rm_miller")
        vehicle_number = st.text_input("Vehicle Number *", placeholder="Type...")
        po_number = st.text_input("PO Number *", placeholder="Type...")
        
    with rc3:
        invoice_number = st.text_input("Invoice Number *", placeholder="Type...")
        gross_qty = st.number_input("Gross Qty *", value=None, step=50.0, placeholder="Type...")
        bag_type = st.selectbox("Bag Type", ["Jute Bag", "Plastic Bag"])
        total_bags = st.number_input("Number Of Total Bags *", value=None, step=10, placeholder="Type...")
        bag_wt = st.number_input("Bag Wt *", value=None, step=0.1, placeholder="Type...")

    # Calculate net weight safely if inputs are provided
    if gross_qty is not None and total_bags is not None and bag_wt is not None:
        net_wt = gross_qty - (total_bags * bag_wt)
        st.info(f"Calculated Net Wt (Gross Qty - [Total Bags * Bag Wt]): **{net_wt:,.2f}**")
    else:
        net_wt = 0.0

    # Mandatory Validation Condition
    is_valid_rm = (
        bool(vendor_name.strip()) 
        and bool(material_name.strip()) 
        and bool(vehicle_number.strip()) 
        and bool(po_number.strip()) 
        and bool(invoice_number.strip()) 
        and gross_qty is not None and gross_qty > 0 
        and total_bags is not None and total_bags > 0 
        and bag_wt is not None and bag_wt > 0
    )

    submit_rm = st.form_submit_button(label="Save Raw Material Entry", disabled=not is_valid_rm)

    if not is_valid_rm:
        st.warning("⚠️ कृपया सभी अनिवार्य फील्ड्स (Vendor, Material, Vehicle, PO, Invoice, Qty, Bags) भरें, तभी सेव बटन चालू होगा।")

    if submit_rm and is_valid_rm:
        try:
            query = """
                INSERT INTO raw_material (entry_date, vendor_name, material_name, miller_name, vehicle_number, po_number, invoice_number, gross_qty, bag_type, total_bags, bag_wt, net_wt, entered_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            with engine.begin() as conn:
                conn.execute(
                    query, 
                    (entry_date, vendor_name.strip(), material_name.strip(), miller_name, vehicle_number.strip(), po_number.strip(), invoice_number.strip(), float(gross_qty), bag_type, int(total_bags), float(bag_wt), round(float(net_wt), 2), current_logged_user)
                )
            st.success("Raw Material Entry Saved Successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving entry: {e}")

st.divider()
st.subheader("Saved Raw Material Records")
try:
    df_rm = pd.read_sql("SELECT * FROM raw_material", engine)
    st.dataframe(df_rm)
except Exception as e:
    st.info("No records found or table doesn't exist yet.")

# --- 2. Quality Entry Section ---
st.subheader("Raw Material Quality Entry")
with st.form("quality_form"):
    qc1, qc2 = st.columns(2)
    with qc1:
        hl = st.number_input("HL (Hectolitre Weight) *", value=None, step=0.1, placeholder="Type...")
        foreign_material = st.number_input("Foreign Material % *", value=None, step=0.01, format="%.2f", placeholder="Type...")
    with qc2:
        moisture = st.number_input("Moisture % *", value=None, step=0.1, format="%.1f", placeholder="Type...")
        visibility = st.text_input("Visibility / Grain Appearance *", placeholder="e.g. Clean / Clear")
        q_invoice = st.text_input("Reference Invoice Number *", placeholder="Type matching invoice...")

    is_valid_q = bool(visibility.strip()) and bool(q_invoice.strip()) and (hl is not None and hl > 0) and (moisture is not None and moisture > 0) and (foreign_material is not None)

    submit_q = st.form_submit_button(label="Save Quality Entry", disabled=not is_valid_q)

    if not is_valid_q:
        st.warning("⚠️ कृपया सभी क्वालिटी पैरामीटर और Invoice सही से भरें।")

    if submit_q and is_valid_q:
        try:
            query = """
                INSERT INTO raw_material_quality (invoice_number, hl, foreign_material, moisture, visibility, entered_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            with engine.begin() as conn:
                conn.execute(
                    query, 
                    (q_invoice.strip(), float(hl), float(foreign_material), float(moisture), visibility.strip(), current_logged_user)
                )
            st.success("Quality Entry Saved Successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving quality entry: {e}")

st.divider()
st.subheader("Saved Raw Material Quality Records")
try:
    df_q = pd.read_sql("SELECT * FROM raw_material_quality", engine)
    st.dataframe(df_q)
except Exception as e:
    st.info("No quality records found.")
