import os
import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# LangChain සහ AI Imports
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# ඔයාගේ Files වලින් ගන්නා Imports (තිත අයින් කරලා තියෙන්නේ --app-dir src නිසා)
from database import engine, Base, get_db
import models
import auth

from .agent import tourism_agent # අලුත් Agent එක ගේන්න
from langchain_core.messages import HumanMessage

# 1. Environment Variables Load කිරීම
load_dotenv()

# 2. Database Tables නිර්මාණය කිරීම (PostgreSQL වල tables නැත්නම් මේකෙන් හදනවා)
models.Base.metadata.create_all(bind=engine)

# 3. AI Agent එක Setup කිරීම (Server එක Start වෙනකොටම මේක ලෝඩ් වෙනවා)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.5
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_db.as_retriever(search_kwargs={"k": 3})
)

# 4. FastAPI App එක නිර්මාණය කිරීම
app = FastAPI(title="Smart Tourism API 🇱🇰")

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Tourism API"}

# --- 1. User Signup ---
@app.post("/signup")
def signup(username: str, email: str, password: str, db: Session = Depends(get_db)):
    user_exists = db.query(models.User).filter(models.User.email == email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = auth.hash_password(password)
    new_user = models.User(username=username, email=email, password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

# --- 2. User Login ---
@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- 3. AI Chat (සහ Database එකේ සේව් කිරීම) ---
@app.post("/chat")
async def chat_with_ai(user_query: str, user_id: int, db: Session = Depends(get_db)):
    # 1. Agent එක හරහා පිළිතුර ලබා ගැනීම
    inputs = {"messages": [HumanMessage(content=user_query)]}
    result = tourism_agent.invoke(inputs)
    
    # අන්තිමට ලැබුණු message එක AI එකේ උත්තරයයි
    ai_response = result["messages"][-1].content

    # 2. Database එකේ සේව් කිරීම (කලින් කෝඩ් එකමයි)
    new_log = models.ChatLog(user_id=user_id, query=user_query, response=ai_response)
    db.add(new_log)
    db.commit()

    return {"ai_response": ai_response, "status": "Processed by LangGraph Agent"}

    return {
        "user_query": user_query,
        "ai_response": ai_response,
        "status": "Saved to Database"
    }

# --- 4. Chat History ලබා ගැනීම ---
@app.get("/history/{user_id}")
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    history = db.query(models.ChatLog).filter(models.ChatLog.user_id == user_id).all()
    return history