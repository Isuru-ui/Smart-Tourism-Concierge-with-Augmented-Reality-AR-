import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# --- නිවැරදි Imports ---
from database import engine, Base, get_db
import models
import auth
from agent import tourism_agent  # තිත නැතිව Import කිරීම

# 1. Environment Variables
load_dotenv()

# 2. Database Tables
models.Base.metadata.create_all(bind=engine)

# 3. App Setup
app = FastAPI(title="Smart Tourism API 🇱🇰")

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Tourism API"}

# --- Signup ---
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

# --- Login ---
@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Chat ---
@app.post("/chat")
async def chat_with_ai(user_query: str, user_id: int, db: Session = Depends(get_db)):
    # Agent හරහා පිළිතුර ගැනීම
    inputs = {"messages": [HumanMessage(content=user_query)]}
    result = tourism_agent.invoke(inputs)
    ai_response = result["messages"][-1].content

    # Database සේව් කිරීම
    new_log = models.ChatLog(user_id=user_id, query=user_query, response=ai_response)
    db.add(new_log)
    db.commit()

    return {
        "user_query": user_query,
        "ai_response": ai_response,
        "status": "Processed by LangGraph Agent"
    }

# --- History ---
@app.get("/history/{user_id}")
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    history = db.query(models.ChatLog).filter(models.ChatLog.user_id == user_id).all()
    return history