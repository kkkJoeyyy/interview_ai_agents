from transformers import pipeline
import re

# 初始化分类器
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

# 置信度阈值
CONFIDENCE_THRESHOLD = 0.5

def recognize_intent_with_available_kbs(question: str, available_kbs: list) -> tuple:
    """
    基于实际可用知识库进行意图识别
    返回：(匹配的知识库列表, 置信度)
    """
    print(f"[意图识别] 开始识别问题：{question}")
    print(f"[意图识别] 可用知识库：{available_kbs}")
    
    if not available_kbs:
        print("[意图识别] 无可用知识库，返回空结果")
        return [], 0.0
    
    try:
        # 使用BERT进行零样本分类，候选标签就是实际的知识库名称
        result = classifier(
            question,
            candidate_labels=available_kbs,
            multi_label=True
        )
        
        print(f"[意图识别] 分类结果：")
        for label, score in zip(result['labels'], result['scores']):
            print(f"  {label}: {score:.3f}")
        
        # 获取置信度超过阈值的知识库
        high_confidence_kbs = [
            label for label, score in zip(result['labels'], result['scores'])
            if score >= CONFIDENCE_THRESHOLD
        ]
        
        # 计算平均置信度
        if high_confidence_kbs:
            avg_confidence = sum(
                score for label, score in zip(result['labels'], result['scores'])
                if label in high_confidence_kbs
            ) / len(high_confidence_kbs)
        else:
            avg_confidence = result['scores'][0] if result['scores'] else 0.0
        
        print(f"[意图识别] 高置信度知识库：{high_confidence_kbs}")
        print(f"[意图识别] 平均置信度：{avg_confidence:.3f}")
        
        return high_confidence_kbs, avg_confidence
        
    except Exception as e:
        print(f"[意图识别] 分类失败：{e}")
        return [], 0.0

# 保留旧函数以兼容性，但标记为已弃用
def recognize_intent(question: str) -> list:
    """
    已弃用的意图识别函数，请使用 recognize_intent_with_available_kbs
    """
    print("[DEPRECATED] 使用了已弃用的 recognize_intent 函数")
    return []