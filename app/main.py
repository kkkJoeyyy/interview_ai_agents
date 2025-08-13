from fastapi import FastAPI, Request
from knowledge_base.knowledge_manager import add_pdf_to_knowledge_base, search_knowledge_base
from intent_recognition.intent_classifier import recognize_intent
from answer_generation.ali_qianwen import generate_answer_with_qianwen

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import unquote 

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = FastAPI()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")
templates = Jinja2Templates(directory="app/frontend/templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 添加知识库管理接口
from knowledge_base.knowledge_manager import (
    get_all_knowledge_bases, 
    create_knowledge_base as kb_create,
    delete_knowledge_base as kb_delete,
    get_knowledge_base_stats
)

@app.get("/knowledge_bases")
async def get_knowledge_bases():
    """获取所有知识库列表"""
    try:
        kbs = get_all_knowledge_bases()
        return {"status": "success", "data": kbs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/knowledge_bases/stats")
async def get_kb_stats(kb_name: str = None):
    """获取知识库统计信息"""
    try:
        stats = get_knowledge_base_stats(kb_name)
        return {"status": "success", "data": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/create_kb")
async def create_knowledge_base_api(data: dict):
    """创建新知识库"""
    try:
        kb_name = data.get("name")
        if not kb_name:
            return {"status": "error", "message": "知识库名称不能为空"}
        
        result = kb_create(kb_name)
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/delete_kb/{kb_name}")
async def delete_knowledge_base_api(kb_name: str):
    """删除指定知识库"""
    try:
        result = kb_delete(kb_name)
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload_pdf/")
def upload_pdf(pdf_path: str, knowledge_base_name: str = "global"):
    try:
        add_pdf_to_knowledge_base(pdf_path, knowledge_base_name)
        return {"status": "success", "message": f"PDF已添加到{knowledge_base_name}知识库"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/ask/")
def ask_question(question: str):
    decoded_question = unquote(question)
    print(f"[DEBUG] 解码后问题：{decoded_question}")
    
    try:
        # 获取意图列表
        intents = recognize_intent(decoded_question)  # 注意这里使用解码后的问题
        print(f"[DEBUG] 原始意图列表：{intents}")
        
        # 清洗意图结果
        valid_intents = [
            intent.lower().strip() 
            for intent in intents 
            if isinstance(intent, str) and len(intent) > 1
        ]
        valid_intents = list(set(valid_intents))  # 去重
        print(f"[DEBUG] 有效意图列表：{valid_intents}")
        
        # 默认回退逻辑
        if not valid_intents:
            valid_intents = ["global"]
            print("[WARNING] 无有效意图，使用全局知识库")

        # 上下文收集
        context = []
        for intent in valid_intents:
            print(f"[DEBUG] 正在检索知识库：{intent}")
            results = search_knowledge_base(
                query=decoded_question,
                knowledge_base_name=intent,
                top_k=3  # 限制检索数量
            )
            context.extend([doc.page_content for doc in results])
        
        # 生成回答
        return {"answer": generate_answer_with_qianwen("\n".join(context), decoded_question)}
    
    except Exception as e:
        print(f"[ERROR] 处理异常：{str(e)}")
        return {"status": "error", "message": str(e)}