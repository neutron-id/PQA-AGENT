import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality AI Analyst", layout="wide")
st.title("⚡ Power Quality AI Analyst (Pro Edition 2026)")

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
        
        # Ambil 2000 data terakhir untuk analisa mendalam
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

    # --- KONFIGURASI AI (SDK TERBARU) ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Instruksi agar AI langsung menjawab hasil, bukan memberi kode
    instruksi_sistem = f"""
    Anda adalah asisten cerdas Power Quality untuk PT LUCKY INDAH KERAMIK.
    Tugas Anda adalah menganalisis dataframe bernama 'df' yang memiliki kolom: {list(df.columns)}.
    
    ATURAN PENTING:
    1. JANGAN memberikan potongan kode Python kepada user.
    2. Jalankan kode Python secara internal untuk menemukan jawaban.
    3. Jawablah langsung dengan data/angka dan penjelasan singkat dalam Bahasa Indonesia.
    4. Jika ditanya data 'terakhir' atau 'sekarang', gunakan baris paling akhir dari dataset.
    5. Selalu sertakan satuan (Volt, Ampere, kWh, dll).
    """

    prompt = st.chat_input("Tanya apa saja (contoh: Berapa rata-rata tegangan di PM1 hari ini?)")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Sedang menghitung data..."):
                try:
                    # Mengaktifkan FITUR CODE EXECUTION
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", # Gunakan model stabil terbaru
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=instruksi_sistem,
                            tools=[{'code_execution': {}}], # Ini kunci agar tidak muncul kode
                        ),
                    )
                    
                    # Menampilkan jawaban akhir saja
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"Sistem AI sedang sibuk: {e}")
