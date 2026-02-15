import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- SETUP HALAMAN ---
st.set_page_config(page_title="PQA Analyst Gemini 3", layout="wide")
st.title("⚡ Power Quality AI Analyst (PT Lucky Indah Keramik)")

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
    st.success(f"✅ Sistem Aktif: {len(df)} baris data terdeteksi.")

    # --- KONFIGURASI SDK GEMINI 3 ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # KUNCI UTAMA: Kita ambil 30 baris terakhir sebagai sampel nyata untuk AI
    data_sampel = df.tail(30).to_string(index=False)
    
    instruksi_sistem = f"""
    Anda adalah analis energi senior di PT Putra Arga Binangun.
    Tugas Anda adalah menganalisis data Power Quality.
    
    DATA NYATA (30 Baris Terakhir):
    {data_sampel}
    
    ATURAN:
    1. Gunakan data di atas untuk menjawab pertanyaan user.
    2. Jawab langsung dengan angka dan fakta (Bahasa Indonesia).
    3. Jika user bertanya tentang tren atau rata-rata, hitung berdasarkan data yang diberikan.
    4. JANGAN menampilkan kode Python, berikan hasil analisanya saja.
    """

    prompt = st.chat_input("Tanya data Anda (Contoh: Berapa nilai V_avg terakhir?)")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Gemini 3 sedang membaca data..."):
                try:
                    # Menggunakan Gemini 3 Flash Preview
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=instruksi_sistem
                        ),
                    )
                    st.write(response.text)
                except Exception as e:
                    if "429" in str(e):
                        st.error("Kuota harian (20 RPD) atau menit habis. Tunggu sejenak.")
                    else:
                        st.error(f"Kendala teknis: {e}")
