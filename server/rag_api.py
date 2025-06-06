from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embedding_model = OpenAIEmbeddings()
session_vector_stores = {}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    filename = file.filename
    ext = filename.split(".")[-1].lower()

    if ext != "txt":
        return {"error": "Only .txt files are supported."}

    content = await file.read()

    try:
        text = content.decode("utf-8").strip()
    except UnicodeDecodeError:
        return {"error": "Text file decoding failed. Please use UTF-8 encoding."}

    if not text:
        return {"error": "Parsed document is empty. Please check file content."}

    print(f"\n[UPLOAD] session_id: {session_id}")
    print(f"[UPLOAD] filename: {filename}")
    print(f"[UPLOAD] text length: {len(text)}")
    print(f"[UPLOAD] first 300 chars:\n{text[:300]}\n")

    document = Document(page_content=text)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents([document])

    print(f"[UPLOAD] chunk count: {len(chunks)}")

    if not chunks:
        return {"error": "Document split resulted in no chunks."}

    try:
        store = FAISS.from_documents(chunks, embedding_model)
        session_vector_stores[session_id] = store
        print(f"[UPLOAD] vector store saved to session_vector_stores['{session_id}']\n")
        return {"message": "Uploaded and embedded", "session_id": session_id}
    except Exception as e:
        return {"error": f"Embedding failed: {str(e)}"}


class Query(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    session_id: str = Form(...)
):
    print(f"\n[ASK] session_id: {session_id}")
    print(f"[ASK] question: {question}")
    print(f"[ASK] available sessions: {list(session_vector_stores.keys())}")

    if session_id not in session_vector_stores:
        return {"error": "No document uploaded for this session."}

    vector_store = session_vector_stores[session_id]

    llm = ChatOpenAI(model="gpt-4o-2024-05-13")
    prompt = PromptTemplate(
        template="You are a senior developer. Based on the context below, answer the question:\n\nContext: {context}\n\nQuestion: {question}",
        input_variables=["context", "question"]
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 2}),
        chain_type_kwargs={"prompt": prompt},
        chain_type="stuff"
    )

    result = chain.run(question)
    print(f"[ASK] answer:\n{result}\n")

    return {"answer": result}
