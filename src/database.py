from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# PostgreSQL Connection String
# Format: postgresql://[user]:[password]@[host]:[port]/[database_name]
# ඔයා PostgreSQL setup කරනකොට දුන්න password එක මෙතනට දාන්න.
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/tourism_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()