"""
生词本工具 — 收藏单词、查看释义、删除
"""
import json, os, datetime, re
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "vocabulary.json"


def _load() -> list[dict]:
    if not _DATA_PATH.exists():
        return []
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("words", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save(words: list[dict]):
    _DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump({"description": "用户收藏的生词本", "words": words}, f, ensure_ascii=False, indent=2)


def _fetch_definition(word: str) -> str:
    """调用 LLM 获取单词的中文释义"""
    try:
        from src.agent.llm import LLM
        llm = LLM()
        prompt = f"请给出单词「{word}」在四六级考试中最常见的中文释义（1-2个意思），以及一个简单例句（中英对照）。格式：\\n释义：...\\n例句：..."
        result = llm.chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=200)
        return result.strip()
    except Exception:
        return ""


def save_word(word: str) -> str:
    """收藏一个单词（自动获取中文释义）"""
    word = word.strip().lower()
    if not word:
        return "请输入要收藏的单词"
    if not word.isalpha():
        return "请输入有效的英文单词"

    words = _load()
    existing = [w for w in words if w["word"] == word]
    if existing:
        return f"「{word}」已在生词本中"

    # 先保存（无释义），再异步获取释义
    entry = {
        "word": word,
        "definition": "获取中...",
        "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    words.append(entry)
    _save(words)

    # 获取释义（同步，约1-2秒）
    definition = _fetch_definition(word)
    if definition:
        for w in words:
            if w["word"] == word:
                w["definition"] = definition
                break
        _save(words)
        return f"✅ 已收藏「{word}」 — {definition.split(chr(10))[0] if chr(10) in definition else definition[:40]}"
    return f"✅ 已收藏「{word}」"


def get_definition(word: str) -> str:
    """获取已收藏单词的释义"""
    words = _load()
    for w in words:
        if w["word"] == word.lower():
            return w.get("definition", "")
    return ""


def refresh_definition(word: str) -> str:
    """刷新单个单词的释义"""
    word = word.strip().lower()
    definition = _fetch_definition(word)
    if definition:
        words = _load()
        for w in words:
            if w["word"] == word:
                w["definition"] = definition
                break
        _save(words)
    return definition or "获取失败"


def delete_word(word: str) -> str:
    word = word.strip().lower()
    words = _load()
    before = len(words)
    words = [w for w in words if w["word"] != word]
    if len(words) == before:
        return f"「{word}」不在生词本中"
    _save(words)
    return f"🗑️ 已删除「{word}」"


def list_words() -> str:
    """列出所有收藏的单词（含释义）"""
    words = _load()
    if not words:
        return "📭 生词本为空，查单词时可以收藏"

    lines = ["## 📚 我的生词本", "", f"共 {len(words)} 个单词", ""]
    for i, w in enumerate(words, 1):
        word = w["word"]
        definition = w.get("definition", "")
        saved_at = w.get("saved_at", "?")
        if definition:
            lines.append(f"{i}. **{word}** — {definition.split(chr(10))[0][:60]}")
        else:
            lines.append(f"{i}. **{word}** — *收藏于 {saved_at}*")
    return "\n".join(lines)


def get_words_list() -> list[dict]:
    return _load()


# ── 工具注册信息 ──
SAVE_WORD_TOOL = {
    "name": "save_word",
    "description": "收藏一个单词到生词本，自动获取中文释义，用于用户查单词后保存以便复习。",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "要收藏的英文单词"
            }
        },
        "required": ["word"]
    }
}

DELETE_WORD_TOOL = {
    "name": "delete_word",
    "description": "从生词本中删除一个已收藏的单词。",
    "parameters": {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "要删除的英文单词"
            }
        },
        "required": ["word"]
    }
}

LIST_WORDS_TOOL = {
    "name": "list_words",
    "description": "查看生词本中所有已收藏的单词列表（含中文释义）。",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}
