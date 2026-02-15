import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality AI Analyst", layout="wide")
st.title("⚡ Power Quality AI Analyst (Gemini 2 Flash Edition)")

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
        
        # Ambil seluruh data untuk analisa mendalam
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

    # --- KONFIGURASI AI (GEMINI 2 FLASH) ---
    # Menggunakan model dengan kuota 1.500 RPD agar bebas macet
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    instruksi_sistem = f"""
    Anda adalah analis energi profesional untuk PT LUCKY INDAH KERAMIK.
    Dataset Anda adalah dataframe bernama 'df' dengan kolom: {list(df.columns)}.
    
    TUGAS ANDA:
    1. JANGAN memberikan jawaban berupa kode Python.
    2. Gunakan fitur Code Execution untuk menghitung atau memproses data secara internal.
    3. Jawab pertanyaan user langsung dengan angka, fakta, dan penjelasan singkat (Bahasa Indonesia).
    4. Selalu sertakan satuan yang relevan (misal: kWh, Volt, Ampere).
    5. Jika ditanya data terbaru, gunakan baris paling akhir di dataframe.
    """

    prompt = st.chat_input("Tanya data energi atau tegangan (Contoh: Berapa total kWh PM1 hari ini?)")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Menganalisa data menggunakan Gemini 2 Flash..."):
                try:
                    # Eksekusi dengan model Gemini 2 Flash (Jalur 1.5K RPD)
                    response = client.models.generate_content(
                        model="gemini-2-flash", 
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=instruksi_sistem,
                            tools=[{'code_execution': {}}], 
                        ),
                    )
                    
                    # Menampilkan hasil akhir dari proses pemikiran AI
                    st.write(response.text)
                    
                except Exception as e:
                    if "429" in str(e):
                        st.error("Antrean penuh (RPM Limit). Tunggu 15 detik lalu coba lagi.")
                    else:
                        st.error(f"Terjadi kendala teknis: {e}")
