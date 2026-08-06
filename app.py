import datetime
import random
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
    "<p style='text-align: center; color: #555; font-size: 16px;'>Modular"
    " Enterprise MIS with SQLite Storage</p>",
    unsafe_allow_html=True,
)
st.divider()

# --- Database Connection ---
conn = sqlite3.connect("flour_mill_erp.db", check_same_thread=False)
cursor = conn.cursor()


# Initialize Database Tables
def init_db():
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS milling_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milling_date TEXT,
            batch_code TEXT,
            miller_name TEXT,
            item_name TEXT,
            quantity REAL
        )
    """)
  conn.commit()


init_db()

# --- Sidebar Menu ---
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Milling Entry",
        "Month-wise Summary Dashboard",
        "Quality & FG Section",
    ],
)


# --- Helper Function for Auto Batch Code ---
def generate_batch_code(milling_date):
  date_str = str(milling_date).replace("-", "")
  random_suffix = random.randint(100, 999)
  return f"BATCH-{date_str}-{random_suffix}"


# --- 1. MILLING ENTRY SECTION ---
if menu == "Milling Entry":
  st.header("Milling Production Entry")

  with st.form("milling_form"):
    milling_date = st.date_input(
        "Milling Date", value=datetime.date.today()
    )

    # Auto-generate batch code preview based on selected date
    generated_batch = generate_batch_code(milling_date)
    st.info(f"Auto-Generated Batch Code for this entry: **{generated_batch}**")

    miller_name = st.text_input("Miller Name")
    item_name = st.text_input("Item / Raw Material Name")
    quantity = st.number_input("Quantity (Quintals/Kg)", min_value=0.0)

    submit_btn = st.form_submit_button("Save Milling Entry")

    if submit_btn:
      if miller_name and item_name:
        cursor.execute(
            """
                    INSERT INTO milling_entries (milling_date, batch_code, miller_name, item_name, quantity)
                    VALUES (?, ?, ?, ?, ?)
                """,
            (
                str(milling_date),
                generated_batch,
                miller_name,
                item_name,
                quantity,
            ),
        )
        conn.commit()
        st.success(
            f"Entry saved successfully! Batch Code: {generated_batch}"
        )
      else:
        st.warning("Please fill all required fields.")

  # Show existing entries so data is not lost
  st.subheader("Existing Milling Entries")
  df_existing = pd.read_sql_query(
      "SELECT * FROM milling_entries ORDER BY id DESC", conn
  )
  if not df_existing.empty:
    st.dataframe(df_existing, use_container_width=True)
  else:
    st.info("No milling entries found yet.")


# --- 2. MONTH-WISE SUMMARY DASHBOARD ---
elif menu == "Month-wise Summary Dashboard":
  st.header("Executive Month-wise Summary & Stock Dashboard")

  df_milling = pd.read_sql_query("SELECT * FROM milling_entries", conn)

  if df_milling.empty:
    st.info(
        "Pehle kuch data entries karein tab dashboard show hoga ya Milling"
        " Entry section se data bharein."
    )
  else:
    df_milling["Month-Year"] = pd.to_datetime(
        df_milling["milling_date"]
    ).dt.strftime("%B %Y")
    selected_month = st.selectbox(
        "Select Month", df_milling["Month-Year"].unique()
    )

    filtered_month_df = df_milling[
        df_milling["Month-Year"] == selected_month
    ]
    st.dataframe(filtered_month_df, use_container_width=True)


# --- 3. QUALITY & FG SECTION (Batch-wise Linkage) ---
elif menu == "Quality & FG Section":
  st.header("Quality & Finished Goods (FG) View")

  df_milling = pd.read_sql_query("SELECT * FROM milling_entries", conn)

  if df_milling.empty:
    st.warning("No milling batches available. Please add a milling entry first.")
  else:
    # Select specific milling batch to view corresponding quality/FG details
    batch_list = df_milling["batch_code"].unique().tolist()
    selected_batch = st.selectbox(
        "Select Milling Batch Code",
        batch_list,
        help=(
            "Select a batch to view its specific details for Quality and"
            " Finished Goods"
        ),
    )

    # Filter data for the selected batch
    batch_data = df_milling[df_milling["batch_code"] == selected_batch]

    st.markdown(f"### Details for Batch: `{selected_batch}`")
    st.dataframe(batch_data, use_container_width=True)

    # Here you can add inputs for Quality and Finished Goods linked to this batch
    st.info(
        "Aap upar select kiye gaye batch code ke liye yahan Quality parameters"
        " ya Finished Goods ki entries aage jod sakte hain."
    )
