import streamlit as st
import sqlite3
import datetime
import pandas as pd

# Sabse pehle database connection aur helper functions hote hain
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

# Yahan sidebar mein menu define hota hai (Ye hona zaroori hai)
st.sidebar.title("Navigation")
menu = st.sidebar.selectbox("Go to", ["1. Dashboard", "2. Milling Entry", "3. Finished Goods & Yield"])
