"""
六级翻译参考译文查询工具
"""
import json, os, re
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "translations.json"
_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "data" / "translations_template.json"


def _load_translations() -> dict:
    """加载翻译数据"""
    path = _DATA_PATH if _DATA_PATH.exists() else _TEMPLATE_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"description": "", "total": 0, "translations": {}}


def list_available_exams() -> list[str]:
    """列出所有可用的考试名称"""
    data = _load_translations()
    return sorted(data.get("translations", {}).keys(), reverse=True)


def get_translation(exam_name: str) -> str:
    """
    查询指定考试的翻译原文和参考译文

    参数:
        exam_name: 考试名称，如 "2023年6月第1套cet6"

    返回:
        Markdown 格式的查询结果
    """
    data = _load_translations()
    trans = data.get("translations", {})

    # 精确匹配
    if exam_name in trans:
        sets_list = trans[exam_name]
        return _format_translation_result(exam_name, sets_list)

    # 模糊匹配
    matches = [k for k in trans if exam_name in k]
    if not matches:
        # 尝试匹配年份+级别
        pat = exam_name.lower().replace(" ", "").replace("cet6", "").replace("cet-6", "")
        matches = [k for k in trans if pat in k.replace(" ", "").lower()]

    if not matches:
        all_exams = sorted(trans.keys(), reverse=True)
        if all_exams:
            hint = "\n".join(f"  • {e}" for e in all_exams[:10])
            return f"没有找到「{exam_name}」，可用的考试有：\n\n{hint}"
        return f"📭 翻译数据暂未收录。数据收集中..."

    # 如果匹配到多个，展示所有
    results = []
    for m in sorted(matches, reverse=True):
        sets_list = trans[m]
        results.append(_format_translation_result(m, sets_list))
    return "\n\n---\n\n".join(results)


def _format_translation_result(exam_name: str, sets_list: list) -> str:
    """格式化一套考试的翻译结果"""
    lines = [f"## 📖 {exam_name} 翻译参考译文"]

    for i, item in enumerate(sets_list, 1):
        cn = item.get("chinese", "").strip()
        en = item.get("english", "").strip()
        topic = item.get("topic", "")
        source = item.get("source", "")

        if topic:
            lines.append(f"\n### 第{i}套 — {topic}\n")
        else:
            lines.append(f"\n### 第{i}套\n")

        lines.append("**中文原文：**")
        lines.append(f"> {cn}")
        lines.append("")
        lines.append("**参考译文：**")
        lines.append(f"> {en}")

        if source and "参考译文" not in source:
            lines.append(f"\n*来源：{source}*")

    return "\n".join(lines)


TRANSLATION_LOOKUP_TOOL = {
    "name": "translation_lookup",
    "description": "查询六级翻译真题的原文和官方参考译文。支持精确或模糊查询考试名称。",
    "parameters": {
        "type": "object",
        "properties": {
            "exam_name": {
                "type": "string",
                "description": "考试名称，如：2023年6月第1套cet6"
            }
        },
        "required": ["exam_name"]
    }
}


if __name__ == "__main__":
    available = list_available_exams()
    print(f"可用考试: {len(available)} 个")
    for e in available[:5]:
        print(f"  {e}")
