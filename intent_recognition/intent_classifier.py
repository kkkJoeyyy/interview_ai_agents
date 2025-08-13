from transformers import pipeline
import re

# 初始化分类器
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

# 知识库类别列表
kb_categories = ["java", "network", "database", "system-design", "algorithm"]

def recognize_intent(question: str) -> list:
    """混合策略意图识别函数"""
    print(f"[意图识别] 开始识别问题：{question}")
    
    # 策略1：规则匹配（硬编码）
    rule_patterns = {
        "java": [r'\b(java|jvm|spring|hibernate|jdk|jre)\b', r'多线程|垃圾回收|类加载'],
        "network": [r'\b(tcp|udp|http|https|ip|dns|network|router|switch|三次握手|四次挥手)\b', r'协议|握手|挥手|端口'],
        "database": [r'\b(sql|mysql|oracle|database|db|nosql|索引|事务)\b', r'ACID|CAP定理|数据库设计'],
        "system-design": [r'\b(design|architecture|microservice|scalability|微服务|分布式)\b', r'系统架构|高并发|高可用'],
        "algorithm": [r'\b(algorithm|sort|search|tree|graph|complexity|排序|查找)\b', r'时间复杂度|空间复杂度|算法优化']
    }
    
    matched_categories = []
    print(f"[意图识别] 开始硬编码规则匹配")
    
    for category, patterns in rule_patterns.items():
        for pattern in patterns:
            if re.search(pattern, question, re.IGNORECASE):
                matched_categories.append(category)
                print(f"[意图识别] 硬编码匹配成功：{category} (模式: {pattern})")
                break
    
    if matched_categories:
        print(f"[意图识别] 硬编码识别成功，匹配到：{matched_categories}")
        return list(set(matched_categories))  # 去重
    
    # 策略2：模型分类（如果规则匹配失败）
    print(f"[意图识别] 硬编码识别失败，开始BERT相似度识别")
    try:
        result = classifier(
            question,
            candidate_labels=kb_categories,
            multi_label=True
        )
        # 取置信度大于0.5的标签
        high_confidence_labels = [
            label for label, score in zip(result['labels'], result['scores'])
            if score > 0.5
        ]
        if high_confidence_labels:
            print(f"[意图识别] BERT识别成功：{high_confidence_labels}")
            return high_confidence_labels
        else:
            print(f"[意图识别] BERT识别置信度过低，使用最高分：{result['labels'][0]}")
            return [result['labels'][0]]
    except Exception as e:
        print(f"[意图识别] 模型分类失败: {e}")
        print(f"[意图识别] 使用默认知识库：global")
        return ["global"]