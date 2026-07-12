"""
作文模板查询工具 — 按级别和类型筛选模板
"""
import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "essay_templates.json"


def _load() -> dict:
    if not _DATA_PATH.exists():
        return {"templates": {}}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"templates": {}}


def list_levels() -> list[str]:
    """返回可用级别列表"""
    data = _load()
    return [k for k in data.get("templates", {}) if k != "description"]


def list_types(level: str) -> list[str]:
    """返回某级别下的作文类型"""
    data = _load()
    templates = data.get("templates", {})
    if level in templates:
        return [k for k in templates[level]]
    return []


def get_template(level: str, type_name: str) -> dict:
    """获取指定级别和类型的模板"""
    data = _load()
    templates = data.get("templates", {})
    level_data = templates.get(level, {})
    return level_data.get(type_name, {})


def format_template_preview(level: str, type_name: str) -> str:
    """将模板格式化为可读的 Markdown"""
    tpl = get_template(level, type_name)
    if not tpl:
        return f"未找到「{level} - {type_name}」模板"

    lines = []
    lines.append(f"## 📝 {type_name}（{tpl.get('level', level)}）")
    lines.append("")
    lines.append(f"**适用场景：** {tpl.get('description', '')}")
    lines.append("")
    lines.append(f"**结构：** {tpl.get('structure', '')}")
    lines.append("")

    # 模板句式
    t = tpl.get("template", {})
    if t:
        lines.append("### 开头段模板")
        for i, s in enumerate(t.get("opening", []), 1):
            lines.append(f"{i}. `{s}`")
        lines.append("")

        lines.append("### 主体段模板")
        for key, label in [("body", "论证"), ("body_advantages", "优点"), ("body_disadvantages", "缺点"),
                          ("body_causes", "原因分析"), ("body_effects", "影响分析"),
                          ("body_example", "举例论证"), ("body_depth", "深层分析"),
                          ("body_data", "数据描述"), ("body_reasons", "原因分析"),
                          ("concession", "让步段")]:
            if key in t:
                lines.append(f"**{label}：**")
                for i, s in enumerate(t[key], 1):
                    lines.append(f"{i}. `{s}`")
                lines.append("")

        lines.append("### 结尾段模板")
        for i, s in enumerate(t.get("closing", []), 1):
            lines.append(f"{i}. `{s}`")
        lines.append("")

    # 完整范文
    example = tpl.get("full_example", {})
    if example:
        lines.append("### 💡 完整范文")
        title = example.get("title", "") or example.get("type", "")
        if title:
            lines.append(f"**{title}**")
            lines.append("")
        for key in ["opening", "body", "body_advantages", "body_disadvantages",
                    "body_causes", "body_effects", "closing",
                    "body_example", "body_depth", "body_data", "body_reasons",
                    "concession", "content"]:
            if key in example:
                lines.append(f"{example[key]}")
                lines.append("")

    return "\n".join(lines)


# ── 工具注册信息 ──
ESSAY_TEMPLATE_TOOL = {
    "name": "essay_template",
    "description": "查询四六级作文模板。按考试级别（cet4/cet6）和作文类型获取模板句式和范文。",
    "parameters": {
        "type": "object",
        "properties": {
            "level": {
                "type": "string",
                "enum": ["cet4", "cet6", "通用"],
                "description": "考试级别"
            },
            "type_name": {
                "type": "string",
                "description": "作文类型，如：观点选择型、利弊分析型等"
            }
        },
        "required": ["level", "type_name"]
    }
}


if __name__ == "__main__":
    for level in list_levels():
        print(f"\n{'='*40}")
        print(f"级别: {level}")
        for t in list_types(level):
            print(f"  - {t}")
        print()
