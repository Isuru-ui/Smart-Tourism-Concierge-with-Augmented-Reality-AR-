import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA


load_dotenv()

def start_chat():
    print("Initializing AI Agent...")

    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    
    if not os.path.exists("./chroma_db"):
        print("Error: Database not found. Please run ingest_data.py first.")
        return

    vector_db = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )

    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",  
        temperature=0.5,
        api_key=os.getenv("GROQ_API_KEY")
    )

    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    print("\n✅ AI Agent is Ready! (Type 'quit' to exit)\n")

  
    while True:
        query = input("You: ")
        
        if query.lower() in ["quit", "exit"]:
            break
        
        if query.strip() == "":
            continue

        print("Thinking...")
        try:
            response = qa_chain.invoke({"query": query})
            print(f"\nAI: {response['result']}\n")
            print("-" * 50)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    start_chat()