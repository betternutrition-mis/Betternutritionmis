import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# Page configuration
st.set_page_config(page_title="Better Nutrition MIS", layout="wide")

st.title("Better Nutrition MIS - Supabase Connected")

# Supabase connection using Streamlit Secrets
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
    st.success("Supabase connection successful!")
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# Session state simulation for current logged user
if "current_logged_user" not in st.session_state:
    st.session_state["current_logged_user"] = "Admin"

current_logged_user = st.session_state["current_logged_user"]

# Helper function for miller input
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
            data = {
                "entry_date": entry_date,
                "vendor_name": vendor_name.strip(),
                "material_name": material_name.strip(),
                "miller_name": miller_name,
                "vehicle_number": vehicle_number.strip(),
                "po_number": po_number.strip(),
                "invoice_number": invoice_number.strip(),
                "gross_qty": float(gross_qty),
                "bag_type": bag_type,
                "total_bags": int(total_bags),
                "bag_wt": float(bag_wt),
                "net_wt": round(float(net_wt), 2),
                "entered_by": current_logged_user,
            }
            supabase.table("raw_material").insert(data).execute()
            st.success("Raw Material Entry Saved Successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving entry: {e}")

st.divider()
st.subheader("Saved Raw Material Records")
try:
    response = supabase.table("raw_material").select("*").execute()
    df_rm = pd.DataFrame(response.data)
    if not df_rm.empty:
        st.dataframe(df_rm)
    else:
        st.info("No records found.")
except Exception as e:
    st.info("No records found or table doesn't exist yet.")
