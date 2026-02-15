import streamlit as st
import pandas as pd
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality AI Analyst", layout="wide")
st.title("⚡ Power Quality AI Analyst (Final Fix 2026)")

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
        
        # Mengambil data terbaru (mendukung hingga 14760+ baris)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data Sheet: {e}")
        return None

df = load_data()

if df is not None:
    st.success(f"✅ Sistem Terhubung. Memproses {len(df)} baris data Power Quality.")
    
    with st.expander("Klik untuk melihat tabel data mentah"):
        st.dataframe(df.tail(10))

    # --- KONFIGURASI AI (GEMINI 2.0 FLASH - KUOTA 1.5K) ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    instruksi_sistem = f"""
    Anda adalah analis energi profesional PT Putra Arga Binangun.
    Dataset Anda adalah dataframe 'df' dengan kolom: {list(df.columns)}.
    
    ATURAN:
    1. JANGAN memberikan jawaban berupa kode Python ke user.
    2. Gunakan fitur 'Code Execution' untuk memproses data secara internal.
    3. Jawab langsung dengan angka/fakta dan penjelasan singkat dalam Bahasa Indonesia.
    4. Selalu sertakan satuan (Volt, Ampere, kWh, dll).
    5. Jika ditanya data terbaru, gunakan data di baris paling akhir.
    """

    prompt = st.chat_input("Tanya data tegangan atau arus PM1...")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Menganalisa data menggunakan Gemini 2.0 Flash..."):
                max_retries = 3
                for i in range(max_retries):
                    try:
                        # Menggunakan model 2.0 Flash dengan jatah 1.5K RPD
                        response = client.models.generate_content(
                            model="gemini-2.0-flash", 
                            contents=[prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=instruksi_sistem,
                                tools=[{'code_execution': {}}], 
                            ),
                        )
                        st.write(response.text)
                        break # Berhasil, keluar dari loop
                        
                    except Exception as e:
                        if "429" in str(e) and i < max_retries - 1:
                            st.warning(f"Antrean penuh. Mencoba lagi dalam 5 detik... (Percobaan {i+1}/{max_retries})")
                            time.sleep(5)
                        elif "404" in str(e):
                            st.error("Model tidak ditemukan. Pastikan nama model 'gemini-2.0-flash' tersedia di wilayah Anda.")
                            break
                        else:
                            st.error(f"Terjadi kendala teknis: {e}")
                            break
