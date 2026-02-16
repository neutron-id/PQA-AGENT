import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from google.genai import types

# --- CONFIG ---
st.set_page_config(page_title="PQA Analyst Pro", layout="wide")
st.title("⚡ Power Quality AI Analyst (Optimized Mode)")

# --- 1. FUNGSI LOAD DATA (DIOPTIMALKAN) ---
@st.cache_data(ttl=300) # Data disimpan di cache selama 5 menit
def get_optimized_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        key_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(st.secrets["SHEET_NAME"]).sheet1
        
        # Ambil data
        records = sheet.get_all_records()
        full_df = pd.DataFrame(records)
        
        # Ringkasan Statistik (Dihitung SEKALI saja di sini)
        total_rows = len(full_df)
        first_row = full_df.iloc[0].to_dict()
        last_row = full_df.iloc[-1].to_dict()
        
        # Ambil hanya kolom angka untuk statistik agar cepat
        num_df = full_df.select_dtypes(include=['number'])
        summary_stats = num_df.agg(['mean', 'max', 'min']).to_dict()
        
        return full_df, total_rows, first_row, last_row, summary_stats
    except Exception as e:
        return None, 0, None, None, str(e)

# Jalankan Load Data
with st.spinner("Sinkronisasi database 14.000+ baris..."):
    df, total, start_data, end_data, stats = get_optimized_data()

if df is not None and not isinstance(df, str):
    st.success(f"✅ Database Sinkron: {total} baris terdeteksi.")

    # --- 2. SETUP AI ---
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Ambil 10 data terbaru saja (lebih ringan dari 30)
    recent_context = df.tail(10).to_string(index=False)
    
    # Masukkan ringkasan ke instruksi (bukan seluruh dataframe!)
    sys_instruct = f"""
    Anda adalah Analis PT Putra Arga Binangun.
    
    RINGKASAN DATABASE:
    - Total Data: {total} baris.
    - Awal Data (Sejarah): {start_data}
    - Akhir Data (Sekarang): {end_data}
    - Statistik Global: {stats}
    
    DATA TERBARU:
    {recent_context}
    
    TUGAS: Jawab pertanyaan user dengan singkat berdasarkan ringkasan di atas.
    Jangan gunakan kode Python. Jawab langsung hasilnya.
    """

    # --- 3. CHAT INTERFACE ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    prompt = st.chat_input("Tanya sejarah data atau kondisi sekarang...")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=[prompt],
                        config=types.GenerateContentConfig(system_instruction=sys_instruct),
                    )
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"AI Timeout/Error: {e}")
else:
    st.error(f"Gagal memuat data. Pesan: {stats}")

# --- 4. GRAFIK (OPSIONAL & RINGAN) ---
if st.button("Tampilkan Grafik Tren (100 Data Terakhir)"):
    st.line_chart(df.select_dtypes(include=['number']).tail(100))
