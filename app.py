import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pandasai import SmartDataframe
from pandasai.llm import GoogleGemini

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality Agent", layout="wide")
st.title("⚡ Power Quality AI Analyst (v3)")

# --- KONEKSI KE GOOGLE SHEETS VIA SECRETS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Membaca credentials dari Streamlit Secrets (Aman untuk Cloud)
        key_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        
        # Buka Sheet berdasarkan nama yang ada di Secrets
        sheet_name = st.secrets["SHEET_NAME"]
        sheet = client.open(sheet_name).sheet1
        
        # Ambil data (Batasi 2000 baris terakhir agar cepat)
        data = sheet.get_all_records()[-2000:]
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error Koneksi: {e}")
        return None

# --- MAIN PROGRAM ---
# Cek apakah secrets sudah diisi
if "GEMINI_API_KEY" not in st.secrets:
    st.warning("⚠️ Harap masukkan Secrets di Dashboard Streamlit terlebih dahulu.")
    st.stop()

df = load_data()

if df is not None:
    st.write(f"✅ Terhubung ke data. Total baris: {len(df)}")
    with st.expander("Lihat Data Terakhir"):
        st.dataframe(df.tail(5))

    # Setup Agent
    llm = GoogleGemini(api_key=st.secrets["GEMINI_API_KEY"], model="gemini-1.5-flash")
    agent = SmartDataframe(df, config={"llm": llm})

    # Chat Interface
    prompt = st.chat_input("Tanya data Power Quality Anda...")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Menganalisa..."):
                try:
                    response = agent.chat(prompt)
                    
                    if isinstance(response, str) and ".png" in response:
                        st.image(response)
                    else:
                        st.write(response)
                except Exception as e:
                    st.error(f"Error: {e}")
