import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# 1. Page Config (Tab එකේ නම)
st.set_page_config(page_title="Smart Tourism Agent", page_icon="🇱🇰")

# 2. Header
st.title("🐘 Smart Tourism AI Agent - Sri Lanka")
st.markdown("I can help you plan your trip to Sri Lanka based on verified local guides!")

# 3. Load Keys
load_dotenv()

# 4. Cache Resource (හැම සැරේම මොඩල් එක ලෝඩ් නොවී වේගවත් කරන්න)
@st.cache_resource
def load_agent():
    # Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Database Connect
    if not os.path.exists("./chroma_db"):
        st.error("Database not found! Please run ingest_data.py first.")
        return None
        
    vector_db = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    
    # LLM Setup (Groq)
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    # RAG Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    return qa_chain

qa_chain = load_agent()

# 5. Chat Interface (Chat History පෙන්වන්න)
if "messages" not in st.session_state:
    st.session_state.messages = []

# කලින් කතා කරපුවා පෙන්වන්න
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. User Input
if prompt := st.chat_input("Ask me about Sri Lanka tourism..."):
    # User ගේ ප්‍රශ්නය පෙන්වන්න
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI එකේ උත්තරේ ගන්න
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            if qa_chain:
                result = qa_chain.invoke({"query": prompt})
                response_text = result['result']
                
                # උත්තරේ පෙන්වන්න
                message_placeholder.markdown(response_text)
                
                # History එකට එකතු කරන්න
                st.session_state.messages.append({"role": "assistant", "content": response_text})