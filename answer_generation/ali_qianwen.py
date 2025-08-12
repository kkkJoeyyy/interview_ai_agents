import os
import dashscope
from dotenv import load_dotenv
from typing import List, Dict

# 加载环境变量
load_dotenv()

# 配置API密钥
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def generate_answer_with_qianwen(context: str, question: str) -> str:
    """使用通义千问生成回答（适配最新主程序）"""
    try:
        # 构建提示词
        prompt = f"""
        [角色] 您是一位资深的Java技术面试官
        [要求]
        1. 根据提供的上下文回答问题
        2. 分点列出核心知识点
        3. 提供Java代码示例（如果适用）
        4. 给出面试回答建议
        
        [上下文]
        {context}
        
        [问题]
        {question}
        """
        
        # 调用生成API
        response = dashscope.Generation.call(
            model="qwen-turbo",
            prompt=prompt,
            top_p=0.8,
            temperature=0.7,
            max_tokens=1500
        )
        
        # 解析响应
        if response.status_code == 200:
            return response.output.choices[0].message.content
        return f"生成失败，状态码：{response.status_code}"
        
    except Exception as e:
        return f"API调用异常：{str(e)}"