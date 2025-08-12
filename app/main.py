from fastapi import FastAPI
from knowledge_base.knowledge_manager import add_pdf_to_knowledge_base, search_knowledge_base
from intent_recognition.intent_classifier import recognize_intent
from answer_generation.ali_qianwen import generate_answer_with_qianwen

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Java面试AI问答系统已启动"}

@app.post("/upload_pdf/")
def upload_pdf(pdf_path: str, knowledge_base_name: str = "global"):
    try:
        add_pdf_to_knowledge_base(pdf_path, knowledge_base_name)
        return {"status": "success", "message": f"PDF已添加到{knowledge_base_name}知识库"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/ask/")
def ask_question(question: str):
    try:
        # 意图识别
        intents = recognize_intent(question)
        
        # 上下文收集
        context = []
        for intent in intents:
            results = search_knowledge_base(question, knowledge_base_name=intent)
            context.extend([doc.page_content for doc in results])
        
        # 生成回答
        answer = generate_answer_with_qianwen("\n".join(context), question)
        return {"answer": answer}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}