import os
from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from database import engine, Base
import models

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, auth
from database import engine, Base, get_db



models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/signup")
def signup(username: str, email: str, password: str, db: Session = Depends(get_db)):
    # කලින් මේ email එක පාවිච්චි කරලා තියෙනවාද බලමු
    user_exists = db.query(models.User).filter(models.User.email == email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Password එක Hash කර සේව් කරමු
    hashed_pwd = auth.hash_password(password)
    new_user = models.User(username=username, email=email, password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

# --- 2. User Login (ඇතුළු වීම) ---
@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Token එකක් සාදා ලබා දීම
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}



load_dotenv()

# --- AI එක ලෝඩ් කරන කොටස (Phase 2 එකේ කෝඩ් එක) ---
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_db.as_retriever(search_kwargs={"k": 3})
)

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Tourism API"}

# මෙන්න මේක තමයි 5 පියවරේ තිබුණ චැට් එකට අදාළ කෝඩ් එක
@app.post("/chat")
async def chat_with_ai(user_query: str):
    # AI එකෙන් පිළිතුර ලබා ගැනීම
    result = qa_chain.invoke({"query": user_query})
    return {
        "user_query": user_query,
        "ai_response": result["result"]
    }