from langdetect import detect
from googletrans import Translator

translator = Translator()

def detect_language(text):
    """检测语言"""
    return detect(text)

def translate_text(text, target_language="en"):
    """翻译文本"""
    return translator.translate(text, dest=target_language).text