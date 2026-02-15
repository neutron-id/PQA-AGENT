# --- SETUP LANGCHAIN AGENT ---
    try:
        # Gunakan nama model tanpa awalan 'models/' karena library sudah menanganinya
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=st.secrets["GEMINI_API_KEY"],
            temperature=0,
            convert_system_message_to_human=True # Membantu kestabilan agen
        )
        
        # Buat Agent
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            verbose=True, 
            allow_dangerous_code=True,
            handle_parsing_errors=True # Penting agar tidak crash jika AI bingung
        )

        # Chat Interface
        prompt = st.chat_input("Tanya data tegangan atau arus PM1...")
        
        if prompt:
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Menganalisa log data..."):
                    try:
                        # Kita gunakan invoke untuk standar LangChain terbaru
                        response = agent.invoke(prompt)
                        st.write(response["output"])
                    except Exception as e:
                        st.error(f"Agent kesulitan: {e}")
