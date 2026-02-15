import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- SETUP HALAMAN ---
st.set_page_config(page_title="PQA Analyst Gemini 3", layout="wide")
st.title("⚡ Power Quality AI Analyst (Gemini 3 Edition)")

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
    st.success(f"✅ Sistem Aktif: {len(df)} baris data terhubung.")

    # --- KONFIGURASI SDK GEMINI 3 ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    instruksi_sistem = f"""
    Anda adalah analis energi senior di PT Putra Arga Binangun.
    Akses Anda adalah dataframe 'df' dengan kolom: {list(df.columns)}.
    
    ATURAN KHUSUS GEMINI 3:
    1. Gunakan 'Code Execution' untuk menganalisa data secara presisi.
    2. Jawab langsung hasilnya, jangan berikan blok kode Python.
    3. Jika ditanya data terbaru, fokus pada baris terakhir.
    4. Bahasa: Indonesia profesional dan ringkas.
    """

    prompt = st.chat_input("Tanya data Anda (Jatah: 20 pertanyaan/hari)...")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Gemini 3 sedang memproses..."):
                try:
                    # MENGGUNAKAN MODEL GEMINI 3 SESUAI PERMINTAAN
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=instruksi_sistem,
                            tools=[{'code_execution': {}}],
                        ),
                    )
                    st.write(response.text)
                except Exception as e:
                    if "429" in str(e):
                        st.error("Kuota Terlampaui (Limit 20 RPD). Tunggu esok hari atau gunakan API Key lain.")
                    else:
                        st.error(f"Kendala teknis Gemini 3: {e}")
