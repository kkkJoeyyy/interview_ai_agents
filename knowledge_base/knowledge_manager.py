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
    """将PDF文件解析并添加到指定知识库（RAG实现）"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"{pdf_path} not found.")
    
    print(f"[RAG] 开始处理PDF文件：{pdf_path}")
    
    # 解析PDF内容
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            text += f"\n[第{page_num+1}页]\n{page_text}"
    
    print(f"[RAG] PDF解析完成，总字符数：{len(text)}")
    
    # RAG文本分块处理
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # 每块1000字符
        chunk_overlap=200,  # 重叠200字符保持上下文
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
    )
    
    chunks = text_splitter.split_text(text)
    print(f"[RAG] 文本分块完成，共{len(chunks)}个片段")
    
    # 创建向量文档
    documents = []
    for i, chunk in enumerate(chunks):
        if chunk.strip():  # 跳过空片段
            # 添加到指定知识库
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": os.path.basename(pdf_path),
                    "knowledge_base": knowledge_base_name,
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "file_path": pdf_path
                }
            )
            documents.append(doc)
            
            # 同时添加到global知识库
            if knowledge_base_name != "global":
                global_doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "knowledge_base": "global",
                        "original_kb": knowledge_base_name,  # 记录原始知识库
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "file_path": pdf_path
                    }
                )
                documents.append(global_doc)
    
    # 批量添加到向量数据库
    if documents:
        vector_store.add_documents(documents)
        print(f"[RAG] 成功添加{len(documents)}个文档片段到向量数据库")
        print(f"[RAG] 目标知识库：{knowledge_base_name}")
        if knowledge_base_name != "global":
            print(f"[RAG] 同时备份到global知识库")
    else:
        print("[RAG] 警告：未生成有效文档片段")
    
    return len(chunks)

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
    

def get_all_knowledge_bases():
    """获取所有知识库列表"""
    try:
        knowledge_bases = set()
        for doc_id in vector_store.index_to_docstore_id.values():
            doc = vector_store.docstore.search(doc_id)
            if doc and hasattr(doc, 'metadata') and 'knowledge_base' in doc.metadata:
                knowledge_bases.add(doc.metadata['knowledge_base'])
        
        # 确保默认知识库存在
        if not knowledge_bases:
            knowledge_bases.add("global")
        
        return sorted(list(knowledge_bases))
    except Exception as e:
        print(f"[ERROR] 获取知识库列表失败：{str(e)}")
        return ["global"]

def create_knowledge_base(kb_name: str):
    """创建新知识库（通过添加标识文档）"""
    try:
        # 验证知识库名称
        if not kb_name or not kb_name.strip():
            raise ValueError("知识库名称不能为空")
        
        kb_name = kb_name.strip().lower()
        
        # 检查是否已存在
        existing_kbs = get_all_knowledge_bases()
        if kb_name in existing_kbs:
            return {"status": "warning", "message": f"知识库 '{kb_name}' 已存在"}
        
        # 确保global知识库始终存在
        if "global" not in existing_kbs:
            global_doc = Document(
                page_content="这是全局知识库，包含所有上传文档的副本。",
                metadata={
                    "source": "system_global_identifier",
                    "knowledge_base": "global",
                    "type": "identifier"
                }
            )
            vector_store.add_documents([global_doc])
            print(f"[CREATE] 重新创建global知识库")
        
        # 创建新知识库标识文档
        identifier_doc = Document(
            page_content=f"这是 {kb_name} 知识库的标识文档。",
            metadata={
                "source": f"system_{kb_name}_identifier",
                "knowledge_base": kb_name,
                "type": "identifier"
            }
        )
        
        vector_store.add_documents([identifier_doc])
        print(f"[CREATE] 成功创建知识库：{kb_name}")
        return {"status": "success", "message": f"知识库 '{kb_name}' 创建成功"}
        
    except Exception as e:
        print(f"[ERROR] 创建知识库失败：{str(e)}")
        return {"status": "error", "message": str(e)}

def delete_knowledge_base(kb_name: str):
    """删除指定知识库（删除所有相关文档）"""
    try:
        # 保护系统知识库
        if kb_name.lower() in ["global", "system"]:
            return {"status": "error", "message": "不能删除系统知识库"}
        
        kb_name = kb_name.strip().lower()
        
        # 查找所有属于该知识库的文档
        docs_to_delete = []
        for doc_id in vector_store.index_to_docstore_id.values():
            doc = vector_store.docstore.search(doc_id)
            if (doc and hasattr(doc, 'metadata') and 
                doc.metadata.get('knowledge_base') == kb_name):
                docs_to_delete.append(doc_id)
        
        if not docs_to_delete:
            return {"status": "warning", "message": f"知识库 '{kb_name}' 不存在或已为空"}
        
        # 删除文档
        vector_store.delete(docs_to_delete)
        print(f"[DELETE] 已删除知识库 '{kb_name}'，共删除 {len(docs_to_delete)} 个文档")
        
        return {"status": "success", "message": f"知识库 '{kb_name}' 删除成功，共删除 {len(docs_to_delete)} 个文档"}
        
    except Exception as e:
        print(f"[ERROR] 删除知识库失败：{str(e)}")
        return {"status": "error", "message": str(e)}

def get_knowledge_base_stats(kb_name: str = None):
    """获取知识库统计信息"""
    try:
        stats = {}
        
        if kb_name:
            # 单个知识库统计
            kb_name = kb_name.strip().lower()
            doc_count = 0
            sources = set()
            
            for doc_id in vector_store.index_to_docstore_id.values():
                doc = vector_store.docstore.search(doc_id)
                if (doc and hasattr(doc, 'metadata') and 
                    doc.metadata.get('knowledge_base') == kb_name):
                    doc_count += 1
                    if 'source' in doc.metadata:
                        sources.add(doc.metadata['source'])
            
            stats[kb_name] = {
                "document_count": doc_count,
                "source_count": len(sources),
                "sources": list(sources)
            }
        else:
            # 所有知识库统计
            for kb in get_all_knowledge_bases():
                doc_count = 0
                sources = set()
                
                for doc_id in vector_store.index_to_docstore_id.values():
                    doc = vector_store.docstore.search(doc_id)
                    if (doc and hasattr(doc, 'metadata') and 
                        doc.metadata.get('knowledge_base') == kb):
                        doc_count += 1
                        if 'source' in doc.metadata:
                            sources.add(doc.metadata['source'])
                
                stats[kb] = {
                    "document_count": doc_count,
                    "source_count": len(sources),
                    "sources": list(sources)
                }
        
        return stats
        
    except Exception as e:
        print(f"[ERROR] 获取统计信息失败：{str(e)}")
        return {}

# 初始化日志
print("[INIT] 知识库初始化完成")
print(f"[INIT] 当前知识库数量：{len(vector_store.index_to_docstore_id)}")
try:
    available_kbs = get_all_knowledge_bases()
    print(f"[INIT] 可用知识库分类：{available_kbs}")
except:
    print("[INIT] 知识库分类获取失败")