"""
单词查询工具 — 在真题中查找单词
"""

from src.rag import CETRag

_rag = None

def get_rag() -> CETRag:
    global _rag
    if _rag is None:
        try:
            _rag = CETRag()
        except FileNotFoundError as e:
            print(f"[警告] {e}")
            _rag = None
    return _rag


def word_lookup(word: str) -> str:
    """
    在四六级真题中查找单词，返回该词出现的真题句子和考试信息。
    
    参数:
        word: 要查询的单词（如 "abandon"）
    
    返回:
        包含该词的真题句子列表，标注出自哪年哪套
    """
    rag = get_rag()
    if not rag:
        return "RAG 索引未加载，请先运行 cet-rag-builder/build_rag.py 构建索引"
    
    results = rag.query(word)
    return rag.format_result(results, word)


# ── 工具注册信息 ──────────────────────────
WORD_LOOKUP_TOOL = {
    "name": "word_lookup",
    "description": "在四六级历年真题中查找一个单词，返回该词出现的原文句子、出自哪年哪套卷子。用于帮助学生理解单词在真实考试中的用法。",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "要查询的英文单词"
            }
        },
        "required": ["word"]
    }
}
