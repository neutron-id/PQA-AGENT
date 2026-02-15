import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pandasai import SmartDataframe
# KITA GANTI IMPORTNYA PAKAI LANGCHAIN (LEBIH STABIL):
from langchain_google_genai import ChatGoogleGenerativeAI

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality Agent", layout="wide")
st.title("⚡ Power Quality AI Analyst (Versi Final)")

# --- KONEKSI KE GOOGLE SHEETS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        key_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        client = gspread.authorize(creds)
        
        sheet_name = st.secrets["SHEET_NAME"]
        sheet = client.open(sheet_name).sheet1
        
        # Ambil 2000 baris terakhir
        data = sheet.get_all_records()[-2000:]
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error Koneksi Sheet: {e}")
        return None

# --- MAIN PROGRAM ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets belum diisi!")
    st.stop()

df = load_data()

if df is not None:
    st.success(f"✅ Data Terhubung: {len(df)} baris data.")
    
    with st.expander("Lihat Sampel Data"):
        st.dataframe(df.tail(5))

    # --- BAGIAN UPDATE: KONEKSI AI VIA LANGCHAIN ---
    # Kita pakai LangChain karena support Gemini Flash terbaru
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=st.secrets["GEMINI_API_KEY"],
        temperature=0
    )
    
    # Masukkan LLM LangChain ke dalam PandasAI
    agent = SmartDataframe(df, config={"llm": llm})

    # Chat Interface
    prompt = st.chat_input("Tanya data Power Quality Anda...")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Sedang menganalisa..."):
                try:
                    response = agent.chat(prompt)
                    
                    # Cek hasil gambar atau teks
                    if isinstance(response, str) and ".png" in response:
                        st.image(response)
                    else:
                        st.write(response)
                except Exception as e:
                    st.error(f"Error: {e}")
