from fastapi import FastAPI, Request, UploadFile, File, Form
from knowledge_base.knowledge_manager import add_pdf_to_knowledge_base, search_knowledge_base, get_all_knowledge_bases
from intent_recognition.intent_classifier import recognize_intent_with_available_kbs
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
async def upload_pdf_file(
    file: UploadFile = File(...),
    knowledge_base_name: str = Form(...)
):
    """上传PDF文件并添加到知识库"""
    try:
        # 验证文件类型
        if not file.filename.lower().endswith('.pdf'):
            return {"status": "error", "message": "只支持PDF格式文件"}
        
        # 验证文件大小 (50MB)
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            return {"status": "error", "message": "文件大小不能超过50MB"}
        
        # 保存临时文件
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # 处理PDF文件
            chunks_count = add_pdf_to_knowledge_base(tmp_file_path, knowledge_base_name)
            return {
                "status": "success", 
                "message": f"PDF文件 '{file.filename}' 已成功上传到 {knowledge_base_name} 知识库，共处理 {chunks_count} 个文本块"
            }
        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        return {"status": "error", "message": f"上传失败: {str(e)}"}

@app.get("/ask/")
def ask_question(question: str):
    decoded_question = unquote(question)
    print(f"[DEBUG] 解码后问题：{decoded_question}")
    
    try:
        # 获取所有可用知识库
        available_kbs = get_all_knowledge_bases()
        print(f"[DEBUG] 系统中可用知识库：{available_kbs}")
        
        # 基于实际知识库进行意图识别
        matched_kbs, confidence = recognize_intent_with_available_kbs(decoded_question, available_kbs)
        print(f"[DEBUG] 匹配的知识库：{matched_kbs}")
        print(f"[DEBUG] 置信度：{confidence:.3f}")
        
        # 根据置信度决定是否使用知识库
        if confidence < 0.5:  # 置信度过低
            print("[WARNING] 置信度过低，使用空上下文基于通用知识回答")
            context = ""
        elif not matched_kbs:  # 没有匹配的知识库
            print("[WARNING] 无匹配知识库，使用空上下文基于通用知识回答")
            context = ""
        else:
            # 从匹配的知识库中检索
            context_list = []
            all_sources = set()
            
            print(f"[DEBUG] 开始检索匹配的知识库：{matched_kbs}")
            
            for kb_name in matched_kbs:
                print(f"[DEBUG] 正在检索知识库：{kb_name}")
                results = search_knowledge_base(
                    query=decoded_question,
                    knowledge_base_name=kb_name,
                    top_k=3  # 每个知识库限制3条结果
                )
                
                # 收集上下文和来源
                for doc in results:
                    context_list.append(doc.page_content)
                    all_sources.add(f"{kb_name}:{doc.metadata.get('source', 'unknown')}")
            
            context = "\n".join(context_list)
            print(f"[DEBUG] 检索完成，共找到{len(context_list)}条结果")
            print(f"[DEBUG] 涉及来源：{list(all_sources)}")
        
        # 生成回答
        answer = generate_answer_with_qianwen(context, decoded_question)
        
        # 添加置信度信息到响应中
        return {
            "answer": answer,
            "confidence": confidence,
            "matched_kbs": matched_kbs,
            "context_length": len(context)
        }
    
    except Exception as e:
        print(f"[ERROR] 处理异常：{str(e)}")
        return {"status": "error", "message": str(e)}