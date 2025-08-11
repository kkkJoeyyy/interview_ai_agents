import dashscope
from dashscope import Generation

def generate_answer(question, contexts, search_results=None):
    """使用阿里千问生成回答"""
    # 构建提示词
    prompt = f"""
    你是一位资深的Java技术面试官，请根据以下知识回答面试问题：
    问题：{question}
    
    相关背景知识：
    {format_contexts(contexts)}
    
    {format_search_results(search_results) if search_results else ""}
    
    回答要求：
    1. 分点列出核心要点
    2. 提供实际代码示例（如果适用）
    3. 解释技术原理
    4. 最后给出面试回答建议
    """
    
    # 调用千问API
    response = Generation.call(
        model="qwen-turbo",
        prompt=prompt,
        api_key="YOUR_API_KEY"  # 替换为实际API密钥
    )
    
    return response.output['text']

def format_contexts(contexts):
    """格式化知识库上下文"""
    return "\n".join([f"• [{ctx['source']}] {ctx['content']}" for ctx in contexts])

def format_search_results(results):
    """格式化搜索结果"""
    return "网络搜索结果：\n" + "\n".join(
        [f"• [{res['url']}] {res['content'][:200]}..." for res in results]
    )