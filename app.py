import json
import streamlit as st
from google.oauth2 import service_account
import gspread

# Page configuration
st.set_page_config(page_title="Better Nutrition MIS", layout="wide")

st.title("Better Nutrition MIS - Google Sheets Connection")


@st.cache_resource
def init_connection():
  # Secrets se poori JSON string uthakar load kar rahe hain
  service_account_info = json.loads(st.secrets["gcp_service_account"]["json_key"])

  creds = service_account.Credentials.from_service_account_info(
      service_account_info,
      scopes=[
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive",
      ],
  )

  # gspread client authorize kar rahe hain
  client = gspread.authorize(creds)
  return client


try:
  # Connection initialize karna
  gc = init_connection()
  st.success("Google Sheets ke sath connection successfully establish ho gaya hai!")

  # Agar aapko koi sheet kholkar data dekhna hai toh yahan likh sakte ho:
  # sheet = gc.open("Aapki_Google_Sheet_Ka_Naam").sheet1
  # data = sheet.get_all_records()
  # st.write(data)

except Exception as e:
  st.error(f"Connection mein error aa raha hai: {e}")
