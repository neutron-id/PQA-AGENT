import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pandasai import SmartDataframe
# Lokasi import yang pasti ada di versi 1.5.15:
from pandasai.llm.google_gemini import GoogleGemini

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality Agent", layout="wide")
st.title("⚡ Power Quality AI Analyst (Fix Final)")

# --- KONEKSI KE GOOGLE SHEETS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        key_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        
        sheet_name = st.secrets["SHEET_NAME"]
        sheet = client.open(sheet_name).sheet1
        
        # Ambil 2000 data terakhir
        data = sheet.get_all_records()[-2000:]
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error Koneksi Sheet: {e}")
        return None

# --- MAIN PROGRAM ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets API Key belum diisi!")
    st.stop()

df = load_data()

if df is not None:
    st.success(f"✅ Data Terhubung: {len(df)} baris.")
    
    with st.expander("Lihat Sampel Data"):
        st.dataframe(df.tail(5))

    # --- SETUP LLM (Trik agar tidak 404) ---
    try:
        # Di versi 1.5.15, parameternya adalah model_name
        llm = GoogleGemini(
            api_key=st.secrets["GEMINI_API_KEY"],
            model_name="gemini-1.5-flash" 
        )
        
        # Inisialisasi Agent
        agent = SmartDataframe(df, config={"llm": llm})

        # Chat Interface
        prompt = st.chat_input("Tanya data Power Quality Anda...")
        
        if prompt:
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Menganalisa..."):
                    try:
                        # Gunakan chat()
                        response = agent.chat(prompt)
                        st.write(response)
                    except Exception as ai_err:
                        # Jika agent.chat gagal, coba tampilkan error detailnya
                        st.error(f"AI Error: {ai_err}")
                        
    except Exception as e:
        st.error(f"Gagal Inisialisasi AI: {e}")
