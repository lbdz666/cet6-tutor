"""
单词查询工具 — 在真题中查找单词
"""
import json

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
    在四六级真题中查找单词，返回结构化 JSON 供 LLM 渲染为学习卡片。

    参数:
        word: 要查询的单词（如 "abandon"）

    返回:
        JSON 格式的结构化数据，包含单词在真题中的用法信息
    """
    rag = get_rag()
    if not rag:
        return json.dumps({"error": "RAG 索引未加载"}, ensure_ascii=False)

    results = rag.query(word)

    # 没查到 → 返回友好提示
    if not results:
        return json.dumps({
            "word": word,
            "total": 0,
            "sentences": [],
            "not_found": True,
            "message": f"😅 没找到「{word}」，试试其他拼写？\n\n我们收录了 21,069 个真题词汇，可能是这个词没在四六级真题中出现过。"
        }, ensure_ascii=False)

    stats = rag.stats(word, results)

    # 提取前6个有代表性的句子
    sentences = []
    seen_exams = set()
    for r in results:
        exam = r.get("exam", "")
        # 尽量选不同出处
        if exam and exam not in seen_exams:
            seen_exams.add(exam)
        sentences.append({
            "text": r["sentence"][:300],
            "exam": exam,
            "year": r.get("year", "")
        })
        if len(sentences) >= 6:
            break

    return json.dumps({
        "word": word,
        "total": len(results),
        "sentences": sentences,
        "by_year": stats.get("by_year", {}),
        "by_exam": stats.get("by_exam", {})
    }, ensure_ascii=False)


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
