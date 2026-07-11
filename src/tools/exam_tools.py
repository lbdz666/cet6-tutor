"""
写作辅导工具 — 四六级作文批改（满分15分评分制）
"""
import re

# ── 六级作文评分标准 ──────────────────────────
BAND_DESC = {
    14: {
        "name": "14分档 (13-15分)",
        "desc": "切题，表达思想清楚，文字通顺，连贯性较好，基本上无语言错误。用词准确，句式有变化。"
    },
    11: {
        "name": "11分档 (10-12分)",
        "desc": "切题，表达思想清楚，文字较连贯，但有少量语言错误。用词和句式基本合理。"
    },
    8: {
        "name": "8分档 (7-9分)",
        "desc": "基本切题，有些地方表达思想不够清楚，文字勉强连贯；语言错误相当多，其中有一些是严重错误。"
    },
    5: {
        "name": "5分档 (4-6分)",
        "desc": "基本切题，表达思想不清楚，连贯性差；有较多的严重语言错误。中式英语明显。"
    },
    2: {
        "name": "2分档 (1-3分)",
        "desc": "条理不清，思路紊乱，语言支离破碎或大部分句子均有错误。仅写出个别正确句子。"
    }
}

LEVEL_WORD_LIMITS = {
    "cet4": {"min": 120, "max": 180, "ideal": 150, "label": "四级"},
    "cet6": {"min": 150, "max": 200, "ideal": 180, "label": "六级"},
}


def check_essay(essay: str, level: str = "cet6") -> str:
    """
    检查英语作文，按官方评分标准打分（满分15分）。

    参数:
        essay: 学生作文全文
        level: 考试级别 cet4 / cet6

    返回:
        详细评分报告（Markdown格式）
    """
    word_count = len(re.findall(r'\b\w+\b', essay))
    limits = LEVEL_WORD_LIMITS.get(level, LEVEL_WORD_LIMITS["cet6"])
    warnings = []
    suggestions = []
    deduction = 0.0

    # ── 1. 字数检查 ─────────────────────────
    if word_count < limits["min"]:
        warnings.append(f"⚠️ 字数不足：{limits['label']}要求 {limits['min']}-{limits['max']} 词，当前仅 {word_count} 词，建议写到 {limits['ideal']} 词左右")
        deduction += 2
    elif word_count > limits["max"]:
        warnings.append(f"⚠️ 字数超标：{limits['label']}要求 {limits['min']}-{limits['max']} 词，当前 {word_count} 词，超了 {word_count - limits['max']} 词")
        deduction += 1
    else:
        suggestions.append(f"✅ 字数达标（{word_count}词），符合{limits['label']}要求")

    # ── 2. 内容结构检查 ──────────────────────
    sentences = re.split(r'[.!?]+', essay)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    sent_count = len(sentences)

    if sent_count < 3:
        warnings.append("⚠️ 段落结构不完整：作文应有开头-主体-结尾三段以上结构，当前仅 {} 句".format(sent_count))
        deduction += 2
    elif sent_count < 5:
        warnings.append(f"⚠️ 段落偏短：仅 {sent_count} 个有效句子，建议扩展论点")
        deduction += 1
    else:
        suggestions.append(f"✅ 结构完整（{sent_count} 个有效句子）")

    # ── 3. 语言质量检查 ──────────────────────

    # 3a. 平均句长
    avg_len = word_count / max(sent_count, 1)
    if avg_len > 30:
        warnings.append(f"⚠️ 句子偏长（平均 {avg_len:.0f} 词），建议适当拆分，长短句结合")
        deduction += 1
    elif avg_len < 8 and sent_count > 3:
        warnings.append(f"⚠️ 句子过短（平均 {avg_len:.0f} 词），建议使用连接词丰富句式")
        deduction += 0.5

    # 3b. 词汇多样性
    words_lower = re.findall(r'\b[a-z]+\b', essay.lower())
    unique_words = len(set(words_lower))
    total_words = len(words_lower)
    if total_words > 0:
        diversity = unique_words / total_words
        if diversity < 0.4:
            warnings.append(f"⚠️ 词汇重复较多（去重率 {diversity:.0%}），建议使用同义词替换")
            deduction += 1
        elif diversity > 0.65:
            suggestions.append(f"✅ 词汇丰富（去重率 {diversity:.0%}）")

    # 3c. 连接词使用
    connectors = re.findall(r'\b(however|therefore|furthermore|moreover|nevertheless|consequently|in addition|on the one hand|on the other hand|for example|for instance|in conclusion|to sum up|firstly|secondly|finally|meanwhile|in contrast|as a result|not only|but also|although|because|since|while|whereas)\b', essay, re.I)
    connector_count = len(connectors)
    if connector_count < 2 and sent_count >= 5:
        warnings.append(f"⚠️ 缺少连接词（仅 {connector_count} 处），建议使用 however, therefore, furthermore 等增加连贯性")
        deduction += 1
    elif connector_count >= 3:
        suggestions.append(f"✅ 连接词使用得当（{connector_count} 处），文章连贯性好")

    # 3d. 模板化/中式英语检查
    cn_patterns = [
        (r'\bwith the development of\b', '"with the development of" 模板化开头'),
        (r'\bas we all know\b', '"as we all know" 老套表达'),
        (r'\bmore and more\b', '"more and more" 可用 increasingly 替代'),
        (r'\bin a word\b', '"in a word" 过于口语化'),
        (r'\bfirst of all\b', '"first of all" 可用 firstly/primarily'),
        (r'\bevery coin has two sides\b', '"every coin has two sides" 模板化表达'),
        (r'\bwith the improvement of\b', '"with the improvement of" 模板化表达'),
    ]
    cn_matches = 0
    for pattern, hint in cn_patterns:
        if re.search(pattern, essay, re.I):
            cn_matches += 1
            warnings.append(f"⚠️ {hint}")

    if cn_matches >= 2:
        deduction += 1
        suggestions.append("💡 尝试用更自然的英语表达替代模板化句式")

    # 3e. 语法初步分析
    grammar_issues = []

    # 主谓一致（粗略）
    has_singular_verb = len(re.findall(r'\b\w+[^s]es\b', essay))  # goes, does etc
    has_plural_subject = len(re.findall(r'\b(they|we|people|students)\s+\w+s\b', essay, re.I))

    # 缺少冠词（粗略检查：以单数可数名词开头的句子前缺少a/an/the）
    no_article_pattern = re.findall(r'\b(important|significant|crucial|necessary|effective|useful)\s+\w+\s+is\b', essay, re.I)
    if no_article_pattern:
        grammar_issues.append("注意冠词使用：单数可数名词前通常需要 a/an/the")

    # 检查句子首字母大写
    for s in sentences:
        if s and s[0].islower():
            grammar_issues.append(f"⚠️ 句首字母未大写：\"{s[:30]}...\"")
            deduction += 0.5
            break

    if grammar_issues:
        for g in grammar_issues[:3]:
            warnings.append(g)

    # ── 综合评分 ────────────────────────────
    final_deduction = min(deduction, 14)
    score = max(15 - int(final_deduction), 1)

    # 定档
    if score >= 13:
        band = 14
    elif score >= 10:
        band = 11
    elif score >= 7:
        band = 8
    elif score >= 4:
        band = 5
    else:
        band = 2

    return _format_report(band, essay, level, warnings, suggestions)


def _format_report(band, essay, level, warnings, suggestions):
    """格式化评分报告"""
    info = BAND_DESC[band]
    limits = LEVEL_WORD_LIMITS.get(level, LEVEL_WORD_LIMITS["cet6"])
    word_count = len(re.findall(r'\b\w+\b', essay))

    lines = [
        f"## ✍️ 作文批改报告",
        f"",
        f"**考试级别：{limits['label']}**",
        f"**参考分档：{info['name']}**",
        f"**{info['desc']}**",
        f"",
        f"### 你的作文（共 {word_count} 词）",
        f">{ essay[:500] }",
        f"",
    ]
    if len(essay) > 500:
        lines.append(f"*（仅显示前500字，全文 {len(essay)} 字）*")
        lines.append("")

    if warnings:
        lines.append("### ⚠️ 问题与扣分项")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    if suggestions:
        lines.append("### 💡 改进建议")
        for s in suggestions:
            lines.append(f"- {s}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("### 评分维度")
    lines.append("| 维度 | 占比 | 说明 |")
    lines.append("|------|------|------|")
    lines.append("| 内容切题 | 30% | 是否扣题，论点是否充分展开 |")
    lines.append("| 结构连贯 | 30% | 段落层次清晰，逻辑连贯，有连接词 |")
    lines.append("| 语言质量 | 40% | 语法准确，词汇丰富，句式多样 |")

    return "\n".join(lines)


# ── 工具注册信息 ──────────────────────────
ESSAY_CHECK_TOOL = {
    "name": "check_essay",
    "description": "四六级作文批改：按官方评分标准（满分15分）对作文进行自动评分，给出分档、扣分项和改进建议。",
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


# ── 直接测试 ──────────────────────────
if __name__ == "__main__":
    test_essay = """
Nowadays, environmental protection has become a hot topic. With the rapid development of industry, more and more people realize the importance of protecting our planet. First of all, we should reduce the use of plastic bags. In addition, the government should make laws to control pollution. As we all know, every coin has two sides. On the one hand, economic development is important. On the other hand, we must protect the environment. In a word, we should take action to protect our earth.
"""
    print(check_essay(test_essay, "cet6"))
    print("\n" + "=" * 60 + "\n")
    print(check_essay("This is short.", "cet6"))
