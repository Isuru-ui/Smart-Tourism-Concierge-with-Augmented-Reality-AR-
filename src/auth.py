from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

# Password Hash කිරීමට අවශ්‍ය සැකසුම්
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT සඳහා රහස්‍ය Key එකක් (ඔයාට කැමති එකක් දෙන්න)
SECRET_KEY = "Isuru20000628"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password එක Hash කරන Function එක
def hash_password(password: str):
    return pwd_context.hash(password)

# Hash කළ Password එක සහ ලැබෙන එක සමානදැයි බලන Function එක
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# JWT Token එකක් සාදන Function එක
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)