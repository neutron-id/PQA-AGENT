import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PQA Analyst Global", layout="wide")
st.title("⚡ Power Quality AI Analyst (Full History Mode)")

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
    # --- PROSES METADATA (Mata Global AI) ---
    total_rows = len(df)
    
    # Deteksi Kolom Waktu Otomatis (Timestamp/Date/Time)
    # Kita ambil baris pertama (Sejarah) dan terakhir (Sekarang)
    first_record = df.iloc[0].to_dict()
    last_record = df.iloc[-1].to_dict()
    
    # Hitung Statistik Sederhana untuk memperkuat analisa AI
    # (Hanya jika kolom tersebut angka)
    numeric_df = df.select_dtypes(include=['number'])
    stats_summary = ""
    if not numeric_df.empty:
        stats_summary = numeric_df.describe().loc[['mean', 'max', 'min']].to_string()

    st.success(f"✅ Sistem Aktif: {total_rows} baris data dari seluruh periode terdeteksi.")

    # --- SETUP GEMINI 3 SDK ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Ambil 20 baris terakhir untuk detail teknis saat ini
    recent_data = df.tail(20).to_string(index=False)
    
    instruksi_sistem = f"""
    Anda adalah Analis Senior Power Quality di PT Putra Arga Binangun (LUCKY INDAH KERAMIK).
    
    INGATAN GLOBAL (Seluruh Dataset):
    - Total Data: {total_rows} baris.
    - Data Pertama Kali Diambil (Record #1): {first_record}
    - Data Paling Baru (Record #{total_rows}): {last_record}
    
    RINGKASAN STATISTIK (Seluruh Data):
    {stats_summary}
    
    DETAIL DATA TERBARU (20 Menit/Baris Terakhir):
    {recent_data}
    
    TUGAS ANDA:
    1. Gunakan 'INGATAN GLOBAL' untuk menjawab pertanyaan tentang sejarah, awal data, atau total durasi monitoring.
    2. Gunakan 'DETAIL DATA TERBARU' untuk menjawab kondisi teknis saat ini.
    3. Gunakan 'RINGKASAN STATISTIK' untuk menjawab pertanyaan tentang rata-rata atau nilai tertinggi sepanjang sejarah.
    4. Jawablah langsung ke intinya dengan Bahasa Indonesia yang profesional.
    5. JANGAN menampilkan kode Python.
    """

    # --- INTERFACE CHAT ---
    prompt = st.chat_input("Tanya apa saja (Contoh: Kapan data pertama diambil? atau Berapa rata-rata V_avg?)")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Gemini 3 sedang menelusuri database..."):
                try:
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
                        st.error("Batas kuota Gemini 3 tercapai. Tunggu 1 menit atau coba lagi besok.")
                    else:
                        st.error(f"Kendala: {e}")

    # --- FITUR TAMBAHAN: VISUALISASI CEPAT ---
    with st.expander("Lihat Tren Tegangan (Auto-Graph)"):
        if 'v_avg' in df.columns or 'V_avg' in df.columns:
            v_col = 'v_avg' if 'v_avg' in df.columns else 'V_avg'
            st.line_chart(df[v_col].tail(100))
        else:
            st.info("Kolom V_avg tidak ditemukan untuk membuat grafik.")
