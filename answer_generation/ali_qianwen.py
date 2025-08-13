import os
import dashscope
from dotenv import load_dotenv
from typing import List, Dict

# 加载环境变量
load_dotenv()

# 配置API密钥
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def generate_answer_with_qianwen(context: str, question: str) -> str:
    """使用通义千问生成回答（增强错误处理）"""
    try:
        print(f"[AI] 开始生成回答")
        print(f"[AI] 问题：{question}")
        print(f"[AI] 上下文长度：{len(context)}")
        
        # 检查API密钥
        if not dashscope.api_key:
            return "错误：API密钥未配置，请检查.env文件中的DASHSCOPE_API_KEY"
        
        # 处理空上下文
        if not context or context.strip() == "":
            context = "抱歉，未找到相关资料，我将基于通用知识回答。"
            print("[AI] 警告：使用空上下文")
        
        # 构建提示词
        prompt = f"""
        [角色] 您是一位资深的技术面试官
        [要求]
        1. 根据提供的上下文回答问题
        2. 分点列出核心知识点
        3. 提供代码示例（如果适用）
        4. 给出面试回答建议
        
        [上下文]
        {context}
        
        [问题]
        {question}
        """
        
        # 调用生成API
        response = dashscope.Generation.call(
            model="qwen-turbo",  # 使用更稳定的模型
            prompt=prompt,
            top_p=0.8,
            temperature=0.7,
            max_tokens=1500
        )
        
        print(f"[AI] API响应状态码：{response.status_code}")
        
        # 增强的响应解析
        if response.status_code == 200:
            if hasattr(response, 'output') and response.output:
                if hasattr(response.output, 'text'):
                    # 直接文本输出
                    print("[AI] 使用text字段")
                    return response.output.text
                elif hasattr(response.output, 'choices') and response.output.choices:
                    # choices格式输出
                    print("[AI] 使用choices字段")
                    choice = response.output.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        return choice.message.content
                    elif hasattr(choice, 'text'):
                        return choice.text
                    else:
                        return str(choice)
                else:
                    print(f"[AI] 未知输出格式：{response.output}")
                    return str(response.output)
            else:
                return "API返回空响应"
        else:
            return f"生成失败，状态码：{response.status_code}，错误信息：{getattr(response, 'message', '未知错误')}"
        
    except Exception as e:
        print(f"[AI] 异常详情：{type(e).__name__}: {str(e)}")
        return f"API调用异常：{str(e)}"