import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai # Import sesuai gambar terbaru Anda

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality AI Analyst", layout="wide")
st.title("⚡ Power Quality AI Analyst (Gemini 3 Edition)")

# --- KONEKSI GOOGLE SHEETS (Tetap Sama) ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        key_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        sheet_name = st.secrets["SHEET_NAME"]
        sheet = client.open(sheet_name).sheet1
        data = sheet.get_all_records()[-2000:]
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error Sheet: {e}")
        return None

df = load_data()

if df is not None:
    st.success(f"✅ Data Terhubung: {len(df)} baris.")
    
    # Inisialisasi Client Baru sesuai Gambar Anda
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

    prompt = st.chat_input("Tanya data tegangan PM1...")
    
    if prompt:
        with st.chat_message("user"): st.write(prompt)

        with st.chat_message("assistant"):
            # Kita suruh Gemini 3 menulis kode Python untuk analisa data
            system_instruction = f"Anda adalah analis data. Data kami memiliki kolom: {list(df.columns)}. Tuliskan kode Python pendek untuk menjawab pertanyaan user menggunakan dataframe 'df'."
            
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview", # Pakai model terbaru dari gambar!
                    contents=[system_instruction, prompt]
                )
                
                # Menampilkan jawaban teks
                st.write(response.text)
                
                # Tips: Nanti kita bisa tambahkan fungsi exec() untuk menjalankan kodenya secara otomatis
            except Exception as e:
                st.error(f"Error AI: {e}")
