import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Power Quality AI Analyst", layout="wide")
st.title("⚡ Power Quality AI Analyst (LangChain Edition)")

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
        
        # Ambil 2000 data terakhir
        data = sheet.get_all_records()[-2000:]
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error Koneksi Sheet: {e}")
        return None

# --- CEK API KEY ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("API Key Gemini tidak ditemukan!")
    st.stop()

df = load_data()

if df is not None:
    st.success(f"✅ Data Terhubung: {len(df)} baris data.")
    
    with st.expander("Lihat Sampel Data"):
        st.dataframe(df.tail(5))

    # --- SETUP LANGCHAIN AGENT ---
    try:
        # Gunakan model gemini-1.5-flash (tanpa prefix models/)
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=st.secrets["GEMINI_API_KEY"],
            temperature=0,
            # Menghindari error parsing pada beberapa versi library
            convert_system_message_to_human=True 
        )
        
        # Buat Agent khusus Pandas
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            verbose=True, 
            allow_dangerous_code=True,
            handle_parsing_errors=True
        )

        # Chat Interface
        prompt = st.chat_input("Tanya data tegangan atau arus PM1...")
        
        if prompt:
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Menganalisa data..."):
                    try:
                        # Gunakan invoke untuk standar terbaru
                        response = agent.invoke(prompt)
                        st.write(response["output"])
                    except Exception as e:
                        # Jika 404 tetap muncul, kita beri instruksi debug
                        if "404" in str(e):
                            st.error("Model 1.5 Flash tidak ditemukan. Pastikan API Key Anda memiliki akses ke model ini di Google AI Studio.")
                        else:
                            st.error(f"Agent kesulitan: {e}")
                        
    except Exception as e:
        st.error(f"Gagal memuat Otak AI: {e}")
