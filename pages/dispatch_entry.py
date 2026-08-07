import streamlit as st
import sqlite3
import datetime

st.markdown("""
    <div class="hero-banner">
        <h1>Daily Dispatch Entry & Management</h1>
        <p>Log outgoing stock dispatches SKU-wise with automatic total weight calculation.</p>
    </div>
""", unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect("flour_mill_erp.db", check_same_thread=False)

BASE_MILLER_LIST = [
    "Shree Balram Agro",
    "IKON ORG.",
    "Sathvik Agro",
    "Satya Naraian Kesho",
    "Tara Grains",
    "Other"
]

selected_option = st.selectbox("Miller Name", BASE_MILLER_LIST, key="disp_ms")
miller_name = selected_option
if selected_option == "Other":
    custom_name = st.text_input("Enter New Miller Name Here", key="disp_cs")
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
        
        # Ensure table and columns exist safely
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispatch (
                id INTEGER PRIMARY KEY AUTOINCREMENT, dispatch_date TEXT, miller_name TEXT, party_name TEXT, vehicle_number TEXT, bags_30kg INTEGER, bags_10kg INTEGER, pouches_5kg INTEGER, other_qty REAL, total_dispatched_wt REAL, remarks TEXT, entered_by TEXT
            )
        """)
        
        for col_q in [
            "ALTER TABLE dispatch ADD COLUMN party_name TEXT",
            "ALTER TABLE dispatch ADD COLUMN bags_30kg INTEGER",
            "ALTER TABLE dispatch ADD COLUMN bags_10kg INTEGER",
            "ALTER TABLE dispatch ADD COLUMN pouches_5kg INTEGER",
            "ALTER TABLE dispatch ADD COLUMN other_qty REAL"
        ]:
            try:
                cursor.execute(col_q)
            except Exception:
                pass

        cursor.execute("""
            INSERT INTO dispatch (dispatch_date, miller_name, party_name, vehicle_number, bags_30kg, bags_10kg, pouches_5kg, other_qty, total_dispatched_wt, remarks, entered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dispatch_date, miller_name, party_name, vehicle_no, bags_30kg, bags_10kg, pouches_5kg, other_qty, round(auto_total_wt, 2), remarks, "Admin"))
        
        conn.commit()
        conn.close()
        st.success(f"Dispatch Entry Successfully Saved! Total Wt: {auto_total_wt:,.2f} kg.")

st.subheader("Saved Dispatch Entries")
conn = get_connection()
try:
    df_disp_saved = pd.read_sql("SELECT * FROM dispatch", conn)
    if not df_disp_saved.empty:
        st.dataframe(df_disp_saved, use_container_width=True)
except Exception:
    st.info("No dispatch records found yet.")
conn.close()
