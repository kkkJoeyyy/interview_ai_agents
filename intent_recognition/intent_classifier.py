from transformers import pipeline
import re

# 初始化分类器
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

# 知识库类别列表
kb_categories = ["java", "network", "database", "system-design", "algorithm"]

def recognize_intent(question: str) -> str:
    """混合策略意图识别函数"""
    # 策略1：规则匹配（硬编码）
    rule_patterns = {
        "java": r'\b(java|jvm|spring|hibernate|jdk|jre)\b',
        "network": r'\b(tcp|udp|http|https|ip|dns|network|router|switch)\b',
        "database": r'\b(sql|mysql|oracle|database|db|nosql)\b',
        "system-design": r'\b(design|architecture|microservice|scalability)\b',
        "algorithm": r'\b(algorithm|sort|search|tree|graph|complexity)\b'
    }
    
    for category, pattern in rule_patterns.items():
        if re.search(pattern, question, re.IGNORECASE):
            return category
    
    # 策略2：模型分类（如果规则匹配失败）
    try:
        result = classifier(
            question,
            candidate_labels=kb_categories,
            multi_label=False
        )
        return result['labels'][0]
    except Exception as e:
        print(f"模型分类失败: {e}")
        return "general"  # 默认返回通用知识库