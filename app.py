import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality AI Analyst", layout="wide")
st.title("⚡ Power Quality AI Analyst (Fix 2026)")

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
        
        # Ambil seluruh data (14760+ baris)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data Sheet: {e}")
        return None

df = load_data()

if df is not None:
    st.success(f"✅ Sistem Terhubung. Memproses {len(df)} baris data.")
    
    with st.expander("Klik untuk melihat tabel data mentah"):
        st.dataframe(df.tail(10))

    # --- KONFIGURASI AI (GEMINI 2.0 FLASH - JATAH 1.5K) ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    instruksi_sistem = f"""
    Anda adalah analis energi profesional. 
    Gunakan dataframe 'df' dengan kolom: {list(df.columns)}.
    
    TUGAS:
    1. JANGAN memberikan jawaban berupa kode Python.
    2. Gunakan 'Code Execution' secara internal untuk menghitung data.
    3. Jawab langsung dengan angka/fakta dan penjelasan singkat dalam Bahasa Indonesia.
    4. Selalu sertakan satuan (kWh, Volt, Ampere).
    """

    prompt = st.chat_input("Tanya data energi atau tegangan...")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Menganalisa menggunakan Gemini 2.0 Flash..."):
                try:
                    # GUNAKAN NAMA MODEL YANG TEPAT (JALUR 1.500 RPD)
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
                    if "404" in str(e):
                        st.error("Model 2.0 Flash tidak ditemukan. Sedang mencoba model alternatif...")
                        # Fallback jika model 2.0 masih transisi di region Anda
                        response = client.models.generate_content(
                            model="gemini-1.5-flash",
                            contents=[prompt],
                            config=types.GenerateContentConfig(system_instruction=instruksi_sistem, tools=[{'code_execution': {}}])
                        )
                        st.write(response.text)
                    elif "429" in str(e):
                        st.error("Antrean penuh. Tunggu 15 detik ya.")
                    else:
                        st.error(f"Kendala: {e}")
