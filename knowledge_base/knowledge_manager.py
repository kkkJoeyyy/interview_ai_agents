from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import os
import PyPDF2

# 初始化向量化模型
model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 方法1：使用 from_documents（推荐）
dummy_doc = Document(page_content="dummy", metadata={"source": "dummy"})
vector_store = FAISS.from_documents([dummy_doc], model)

# 方法2：使用 from_texts（备选）
# vector_store = FAISS.from_texts(
#     ["dummy text"], 
#     model, 
#     metadatas=[{"source": "dummy"}]
# )

# 删除虚拟文档
if vector_store.index_to_docstore_id:
    doc_id = list(vector_store.index_to_docstore_id.values())[0]
    vector_store.delete([doc_id])
    print(f"Deleted dummy document: {doc_id}")

def add_pdf_to_knowledge_base(pdf_path, knowledge_base_name="global"):
    """将PDF文件解析并添加到指定知识库"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} not found.")
    
    # 解析PDF内容
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    # 将文本包装为 Document 对象
    doc = Document(
        page_content=text, 
        metadata={"source": pdf_path, "knowledge_base": knowledge_base_name}
    )
    
    # 添加到 FAISS
    vector_store.add_documents([doc])
    print(f"Added {pdf_path} to {knowledge_base_name} knowledge base.")

def search_knowledge_base(query: str, knowledge_base_name: str = "global", top_k: int = 5):
    # 知识库白名单校验
    valid_knowledge_bases = ["global", "java", "network", "database", "system-design", "algorithm"]
    if knowledge_base_name not in valid_knowledge_bases:
        print(f"[WARNING] 非法知识库名称：{knowledge_base_name}，使用全局知识库")
        knowledge_base_name = "global"
    
    # 添加检索日志
    print(f"[SEARCH] 正在检索知识库：{knowledge_base_name}")
    print(f"[SEARCH] 检索语句：{query}")
    
    try:
        results = vector_store.similarity_search(
            query, 
            k=top_k,
            filter={"knowledge_base": knowledge_base_name}
        )
        print(f"[SEARCH] 找到{len(results)}条结果")
        return results
    except Exception as e:
        print(f"[ERROR] 检索失败：{str(e)}")
        return []
    

# 在knowledge_manager.py末尾添加
print("[INIT] 知识库初始化完成")
print(f"[INIT] 当前知识库数量：{len(vector_store.index_to_docstore_id)}")
print(f"[INIT] 可用知识库分类：{list(set(d.metadata['knowledge_base'] for d in vector_store.docstore._dict.values()))}")