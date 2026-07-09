"""
六级真题答案查询工具
将 2023~2025 年 18 套六级阅读答案与 RAG 真题句子关联
"""

import json
from pathlib import Path

ANSWERS_PATH = Path(__file__).parent.parent.parent / "data" / "answers.json"

_answers_cache = None


def _load_answers() -> dict:
    """加载答案数据"""
    global _answers_cache
    if _answers_cache is not None:
        return _answers_cache

    if not ANSWERS_PATH.exists():
        _answers_cache = {"answers": {}}
        return _answers_cache

    with open(ANSWERS_PATH, "r", encoding="utf-8") as f:
        _answers_cache = json.load(f)
    return _answers_cache


def get_exam_answers(exam_name: str) -> dict | None:
    """
    根据考试名称返回答案。

    参数:
        exam_name: 考试名称，如 "2023年6月第1套cet6"

    返回:
        {"cloze": [...], "sectionB": [...], "reading": [...]} 或 None
    """
    data = _load_answers()
    return data.get("answers", {}).get(exam_name)


def list_available_exams() -> list[str]:
    """列出有答案的所有考试"""
    data = _load_answers()
    return sorted(data.get("answers", {}).keys())


SECTION_NAMES = {
    "cloze": "Section A 选词填空（每题3.55分，10题）",
    "sectionB": "Section B 长篇阅读匹配（每题7.1分，10题）",
    "reading": "Section C 仔细阅读（每题14.2分，10题）",
}


def format_exam_answers(exam: str, section: str = "all") -> str:
    """
    格式化输出答案结果

    返回:
        人类可读的答案字符串
    """
    data = _load_answers()
    all_exams = data.get("answers", {})

    # 精确匹配
    matched = exam if exam in all_exams else None

    # 部分匹配
    if matched is None:
        matches = sorted(e for e in all_exams if exam in e)
        if len(matches) == 1:
            matched = matches[0]
        elif len(matches) > 1:
            lines = [f"🔍 找到 {len(matches)} 套匹配「{exam}」的考试：\n"]
            for m in matches:
                lines.append(f"  • {m}")
            lines.append(f"\n请指定具体考试名称，例如：")
            lines.append(f"  「{matches[0]}」")
            return "\n".join(lines)

    if not matched:
        available = list_available_exams()
        return (
            f"❌ 未找到「{exam}」的答案。\n\n"
            f"当前可查询的考试（共 {len(available)} 套）：\n"
            + "\n".join(f"  {a}" for a in available)
        )

    exam_data = all_exams.get(matched)
    if not exam_data:
        return f"❌ 未找到「{matched}」的答案"

    lines = [f"📋 **{matched} 阅读答案**"]
    lines.append("─" * 40)

    sections_to_show = [section] if section != "all" else ["cloze", "sectionB", "reading"]

    for sec in sections_to_show:
        if sec not in exam_data:
            continue
        answers = exam_data[sec]
        desc = SECTION_NAMES.get(sec, sec)
        lines.append(f"\n**{sec}**")
        lines.append(f"  {desc}")
        lines.append("  " + "  ".join(f"{i+1}. {a}" for i, a in enumerate(answers)))

    lines.append(f"\n💡 查单词时也会自动标注哪些句子出自有答案的试卷。")
    return "\n".join(lines)


# ── 工具注册信息 ──────────────────────────

ANSWER_LOOKUP_TOOL = {
    "name": "answer_lookup",
    "description": "查询六级真题阅读答案（选词填空、长篇阅读匹配、仔细阅读）。输入考试名称如 '2023年6月第1套cet6' 获取答案，也支持输入 '2023年6月' 或 '2023' 进行模糊搜索。",
    "parameters": {
        "type": "object",
        "properties": {
            "exam": {
                "type": "string",
                "description": "考试名称，如 '2023年6月第1套cet6'、'2024年12月'、'2025'"
            },
            "section": {
                "type": "string",
                "enum": ["cloze", "sectionB", "reading", "all"],
                "description": "题型：cloze=选词填空, sectionB=长篇阅读匹配, reading=仔细阅读, all=全部",
                "default": "all"
            }
        },
        "required": ["exam"]
    }
}
