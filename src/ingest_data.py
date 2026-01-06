import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings 
from dotenv import load_dotenv

load_dotenv()

def ingest_docs():
    print("Loading PDFs...")
    
    loader = PyPDFDirectoryLoader("./Data") 
    documents = loader.load()
    print(f"Loaded {len(documents)} pages.")

    print("Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks.")

    
    print("Creating Embeddings (Downloding model)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Saving to ChromaDB...")
    db = Chroma.from_documents(
        chunks, 
        embeddings, 
        persist_directory="./chroma_db"
    )
    print("Data ingestion complete!")

if __name__ == "__main__":
    ingest_docs()