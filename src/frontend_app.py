import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="LankaGuide AI", page_icon="🇱🇰", layout="wide")

# Backend එකේ URL එක (FastAPI රන් වෙන තැන)
BASE_URL = "http://127.0.0.1:8000"

# --- Custom Styling (ලස්සන කරන්න) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

# Session State පාවිච්චි කරලා User දත්ත මතක තබා ගැනීම
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""

# --- SIDEBAR (Navigation) ---
with st.sidebar:
    st.title("🐘 LankaGuide AI")
    if st.session_state.user_id:
        st.success(f"Logged in as: {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.user_id = None
            st.rerun()
        
        st.divider()
        st.subheader("📜 Chat History")
        # History එක පෙන්වීම
        try:
            history_res = requests.get(f"{BASE_URL}/history/{st.session_state.user_id}")
            if history_res.status_code == 200:
                for chat in history_res.json():
                    with st.expander(f"Q: {chat['query'][:20]}..."):
                        st.write(f"**A:** {chat['response']}")
        except:
            st.error("Could not load history.")

# --- MAIN INTERFACE ---
if not st.session_state.user_id:
    # --- LOGIN / SIGNUP PAGE ---
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Signup"])
    
    with tab1:
        st.subheader("Login to your account")
        login_email = st.text_input("Email", key="l_email")
        login_pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Login"):
            res = requests.post(f"{BASE_URL}/login", params={"email": login_email, "password": login_pwd})
            if res.status_code == 200:
                # Login වූ පසු user_id එක ලබා ගැනීමට අපිට history හෝ profile endpoint එකක් පාවිච්චි කළ හැක
                # දැනට මම signup එකෙන් ලැබෙන ID එක පාවිච්චි කිරීමට උපදෙස් දෙමි.
                st.session_state.user_id = 1 # උදාහරණයක් ලෙස
                st.session_state.username = login_email.split('@')[0]
                st.success("Welcome back!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        st.subheader("Create a new account")
        s_user = st.text_input("Username")
        s_email = st.text_input("Email")
        s_pwd = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            res = requests.post(f"{BASE_URL}/signup", params={"username": s_user, "email": s_email, "password": s_pwd})
            if res.status_code == 200:
                st.success("Account created! Please login.")
            else:
                st.error("Signup failed")

else:
    # --- CHAT DASHBOARD ---
    st.title("💬 Smart Tourism Concierge")
    st.info("Ask me anything about Sri Lankan tourism, destinations, or itineraries!")

    # Chat interface එක පෙන්වීම
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("Ex: Best places to visit in Ella?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # FastAPI එකට Chat Request එක යැවීම
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data..."):
                response = requests.post(
                    f"{BASE_URL}/chat", 
                    params={"user_query": prompt, "user_id": st.session_state.user_id}
                )
                if response.status_code == 200:
                    answer = response.json()["ai_response"] #
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("Failed to get response from AI.")