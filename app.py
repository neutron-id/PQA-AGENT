import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- SETUP HALAMAN ---
st.set_page_config(page_title="PQA Analyst 2026", layout="wide")
st.title("⚡ Power Quality AI Analyst (Gemini 2.0 Stable)")

# --- KONEKSI GOOGLE SHEETS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        key_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        sheet_name = st.secrets["SHEET_NAME"]
        sheet = client.open(sheet_name).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return None

df = load_data()

if df is not None:
    st.success(f"✅ Data Terhubung: {len(df)} baris.")

    # --- KONFIGURASI SDK GEMINI 2.0 ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Instruksi agar AI fokus pada data PQA Anda
    instruksi_sistem = f"""
    Anda adalah analis energi untuk PT Putra Arga Binangun.
    Dataset Anda adalah dataframe 'df' dengan kolom: {list(df.columns)}.
    
    ATURAN:
    1. Jawab langsung hasil analisanya, JANGAN berikan kode Python ke user.
    2. Gunakan 'Code Execution' untuk menghitung data secara akurat.
    3. Jika ditanya data terbaru, cek baris paling akhir.
    4. Bahasa: Indonesia yang profesional.
    """

    prompt = st.chat_input("Tanya data energi atau tegangan...")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Gemini 2.0 sedang menganalisa..."):
                try:
                    # Menggunakan model gemini-2.0-flash (Jatah 1.5K RPD)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=instruksi_sistem,
                            tools=[{'code_execution': {}}],
                        ),
                    )
                    st.write(response.text)
                except Exception as e:
                    if "429" in str(e):
                        st.error("Batas menit (15 RPM) tercapai. Tunggu 15 detik ya.")
                    else:
                        st.error(f"Terjadi kendala: {e}")
