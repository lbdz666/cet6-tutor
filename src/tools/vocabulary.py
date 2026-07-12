"""
生词本工具 — 查单词时收藏、浏览、删除
"""
import json, os, datetime
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "vocabulary.json"


def _load() -> list[dict]:
    """加载生词本"""
    if not _DATA_PATH.exists():
        return []
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("words", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save(words: list[dict]):
    """保存生词本"""
    _DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump({"description": "用户收藏的生词本", "words": words}, f, ensure_ascii=False, indent=2)


def save_word(word: str) -> str:
    """收藏一个单词"""
    word = word.strip().lower()
    if not word:
        return "请输入要收藏的单词"
    if not word.isalpha():
        return "请输入有效的英文单词"

    words = _load()
    # 去重
    existing = [w for w in words if w["word"] == word]
    if existing:
        return f"「{word}」已在生词本中"

    words.append({
        "word": word,
        "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    _save(words)
    return f"✅ 已收藏「{word}」"


def delete_word(word: str) -> str:
    """从生词本删除一个单词"""
    word = word.strip().lower()
    words = _load()
    before = len(words)
    words = [w for w in words if w["word"] != word]
    if len(words) == before:
        return f"「{word}」不在生词本中"
    _save(words)
    return f"🗑️ 已删除「{word}」"


def list_words() -> str:
    """列出所有收藏的单词"""
    words = _load()
    if not words:
        return "📭 生词本为空，查单词时可以收藏"

    lines = ["## 📚 我的生词本", "", f"共 {len(words)} 个单词", ""]
    for i, w in enumerate(words, 1):
        lines.append(f"{i}. **{w['word']}** — 收藏于 {w.get('saved_at', '?')}")
    return "\n".join(lines)


def get_words_list() -> list[dict]:
    """返回单词列表（供 UI 使用）"""
    return _load()


# ── 工具注册信息 ──
SAVE_WORD_TOOL = {
    "name": "save_word",
    "description": "收藏一个单词到生词本，用于用户查单词后保存以便复习。",
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
    "description": "查看生词本中所有已收藏的单词列表。",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}
