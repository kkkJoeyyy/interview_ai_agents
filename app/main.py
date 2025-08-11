from fastapi import FastAPI
from knowledge_base.knowledge_manager import add_pdf_to_knowledge_base, search_knowledge_base
from intent_recognition.intent_classifier import recognize_intent
from answer_generation.ali_qianwen import generate_answer_with_qianwen

print("Modules imported successfully!")  # 添加此行

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/upload_pdf/")
def upload_pdf(pdf_path: str, knowledge_base_name: str = "global"):
    add_pdf_to_knowledge_base(pdf_path, knowledge_base_name)
    return {"message": f"PDF added to {knowledge_base_name} knowledge base."}

@app.get("/ask/")
def ask_question(question: str):
    intents = recognize_intent(question)
    context = ""
    for intent in intents:
        results = search_knowledge_base(question, knowledge_base_name=intent)
        context += " ".join([res["text"] for res in results])
    answer = generate_answer_with_qianwen(context, question)
    return {"answer": answer}