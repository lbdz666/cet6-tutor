"""
写作辅导工具 — 作文批改 + 范文参考
"""

import re


def check_essay(essay: str, level: str = "cet6") -> str:
    """
    检查英语作文，返回批改建议。
    
    参数:
        essay: 学生作文全文
        level: 考试级别 cet4 / cet6
    
    返回:
        批改建议文本
    """
    word_count = len(re.findall(r'\b\w+\b', essay))
    
    # 基本统计
    suggestions = []
    suggestions.append(f"📊 基本统计")
    suggestions.append(f"  单词数: {word_count}")
    
    # 字数检查
    if level == "cet4":
        if word_count < 120:
            suggestions.append(f"  ⚠️ 四级作文建议 120-180 词，当前 {word_count} 词，偏短")
        elif word_count > 200:
            suggestions.append(f"  ⚠️ 四级作文建议 120-180 词，当前 {word_count} 词，偏长")
    else:
        if word_count < 150:
            suggestions.append(f"  ⚠️ 六级作文建议 150-200 词，当前 {word_count} 词，偏短")
        elif word_count > 250:
            suggestions.append(f"  ⚠️ 六级作文建议 150-200 词，当前 {word_count} 词，偏长")
    
    # 句子长度
    sents = re.split(r'[.!?]+', essay)
    avg_len = word_count / max(len(sents), 1)
    suggestions.append(f"  平均句长: {avg_len:.0f} 词")
    if avg_len > 25:
        suggestions.append(f"  💡 句子偏长，建议适当拆分，长短句结合")
    
    suggestions.append(f"\n💡 详细批改建议请将作文发给 AI 助教")
    
    return "\n".join(suggestions)


ESSAY_CHECK_TOOL = {
    "name": "check_essay",
    "description": "检查英语作文的基本统计信息（字数、句子长度等），给出初步建议。用于辅导四六级写作。",
    "parameters": {
        "type": "object",
        "properties": {
            "essay": {
                "type": "string",
                "description": "学生作文全文"
            },
            "level": {
                "type": "string",
                "enum": ["cet4", "cet6"],
                "description": "考试级别"
            }
        },
        "required": ["essay"]
    }
}
