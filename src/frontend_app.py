import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="LankaGuide AI", page_icon="🐘", layout="wide")

BASE_URL = "http://127.0.0.1:8000"

# --- Styling ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; text-align: left; border-radius: 10px; }
    .sidebar .sidebar-content { background-color: #eef2f6; }
    </style>
    """, unsafe_allow_html=True)

# Session State Setup
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🐘 LankaGuide AI")
    
    if st.session_state.user_id:
        st.success(f"Logged in as: {st.session_state.username}")
        
        # 1. NEW CHAT BUTTON
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = [] # Screen එක Clear කරන්න
            st.rerun()

        st.divider()

        # 2. LOGOUT
        if st.button("Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        st.subheader("📜 Chat History")
        
        # 3. HISTORY LOADING & CLICKING
        try:
            history_res = requests.get(f"{BASE_URL}/history/{st.session_state.user_id}")
            if history_res.status_code == 200:
                chat_data = history_res.json()
                # අලුත්ම ඒවා උඩින් පෙන්වන්න
                for chat in reversed(chat_data):
                    # Button එකක් විදිහට පෙන්වන්න. Click කළාම ඒ Chat එක Load වෙනවා
                    if st.button(f"💬 {chat['query'][:30]}...", key=chat['id']):
                        # පරණ Chat එක Click කළාම Session එකට දාගන්න
                        st.session_state.messages = [
                            {"role": "user", "content": chat['query']},
                            {"role": "assistant", "content": chat['response']}
                        ]
                        st.rerun()
        except Exception as e:
            st.error("Could not load history.")

# --- MAIN INTERFACE ---
if not st.session_state.user_id:
    # --- LOGIN / SIGNUP TABS (කලින් කෝඩ් එකමයි) ---
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Signup"])
    
    with tab1:
        st.subheader("Login")
        login_email = st.text_input("Email", key="l_email")
        login_pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Login"):
            try:
                res = requests.post(f"{BASE_URL}/login", params={"email": login_email, "password": login_pwd})
                if res.status_code == 200:
                    st.session_state.user_id = 1  # Example ID
                    st.session_state.username = login_email.split('@')[0]
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except:
                st.error("Connection Error. Check Backend.")

    with tab2:
        st.subheader("Signup")
        s_user = st.text_input("Username")
        s_email = st.text_input("Email")
        s_pwd = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            try:
                res = requests.post(f"{BASE_URL}/signup", params={"username": s_user, "email": s_email, "password": s_pwd})
                if res.status_code == 200:
                    st.session_state.user_id = res.json()["user_id"]
                    st.session_state.username = s_user
                    st.success("Account created!")
                    st.rerun()
                else:
                    st.error("Signup failed")
            except:
                st.error("Connection Error.")

else:
    # --- CHAT AREA ---
    st.title("Smart Tourism Concierge")

    # මැසේජ් පෙන්වීම
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input Handling
    if prompt := st.chat_input("Ask about Sri Lanka..."):
        # 1. User Message එක පෙන්වන්න
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Backend එකට Request යැවීම (History එකත් එක්ක)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # මෙන්න වෙනස් කරපු තැන: JSON Body එකක් විදිහට යවනවා
                    payload = {
                        "user_query": prompt,
                        "user_id": st.session_state.user_id,
                        "history": st.session_state.messages[:-1] # අන්තිම මැසේජ් එක ඇරෙන්න පරණ ඒවා ටික යවනවා
                    }
                    
                    response = requests.post(f"{BASE_URL}/chat", json=payload)
                    
                    if response.status_code == 200:
                        answer = response.json()["ai_response"]
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection Failed: {e}")