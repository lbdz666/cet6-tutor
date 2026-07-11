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
    shortfall = limits["min"] - word_count
    if word_count < limits["min"]:
        if shortfall <= 10:
            warnings.append(f"⚠️ 字数略少：{limits['label']}要求 {limits['min']}-{limits['max']} 词，当前 {word_count} 词，建议写到 {limits['ideal']} 词左右")
            deduction += 0.5
        elif shortfall <= 50:
            warnings.append(f"⚠️ 字数不足：{limits['label']}要求 {limits['min']}-{limits['max']} 词，当前仅 {word_count} 词，建议写到 {limits['ideal']} 词左右")
            deduction += 2
        else:
            warnings.append(f"⚠️ 严重字数不足：{limits['label']}要求 {limits['min']}-{limits['max']} 词，当前仅 {word_count} 词，差 {shortfall} 词")
            deduction += 3
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

    # ── 3e. 语法检查（全面版）─────────────────
    grammar_issues = []
    grammar_error_count = 0

    # ── 检查函数辅助 ──
    def add_grammar_issue(msg, count=1):
        grammar_issues.append(msg)
        return count

    # ── 1. 主谓一致 ──
    sv = (
        re.findall(r'\b(we|you|they)\s+is\b', essay, re.I) +
        re.findall(r'\b(we|you|they)\s+was\b', essay, re.I) +
        re.findall(r'\b(we|you|they)\s+has\b', essay, re.I) +
        re.findall(r'\b(he|she|it)\s+are\b', essay, re.I) +
        re.findall(r'\b(he|she|it)\s+were\b', essay, re.I) +
        re.findall(r'\b(he|she|it)\s+have\b', essay, re.I) +
        re.findall(r'\bI\s+(is|are|was)\b', essay, re.I) +
        re.findall(r'\b(my|your|his|her|our|their)\s+\w+\s+are\b', essay, re.I)
    )
    if sv:
        grammar_error_count += add_grammar_issue(f"⚠️ 主谓不一致 {len(sv)} 处（如：'{sv[0][0]}...'）", len(sv))

    # ── 2. 情态动词错误 ──
    modal = (
        re.findall(r'\b(can|could|will|would|shall|should|may|might|must)\s+\w+ed\b', essay, re.I) +
        re.findall(r'\b(can|could|will|would|shall|should|may|might|must)\s+\w+ing\b', essay, re.I) +
        re.findall(r'\b(can|could|will|would|shall|should|may|might|must)\s+to\s+\w+\b', essay, re.I)
    )
    if modal:
        grammar_error_count += add_grammar_issue(f"⚠️ 情态动词错误 {len(modal)} 处（情态动词后应跟动词原形）", len(modal))

    # ── 3. 否定句错误 (didn't + 过去式) ──
    neg = re.findall(r"\b(didn't|did not|doesn't|does not|don't|do not)\s+\w+ed\b", essay, re.I)
    if neg:
        grammar_error_count += add_grammar_issue(f"⚠️ 否定句式错误 {len(neg)} 处（否定词后应跟动词原形）", len(neg))

    # ── 4. "there have/has" → 应为 there is/are ──
    there_have = re.findall(r'\bthere\s+(have|has)\b', essay, re.I)
    if there_have:
        grammar_error_count += add_grammar_issue(f"⚠️ '{there_have[0][0]}' 用法错误：表达'存在有'应用 there is/are，不是 there have/has", len(there_have))

    # ── 5. Although/but 同句 ──
    for s in sentences:
        if re.search(r'\b(although|though|even though|even if)\b', s, re.I) and re.search(r'\bbut\b', s, re.I):
            grammar_error_count += add_grammar_issue("⚠️ 句式错误：although/though 和 but 不能同时出现在同一句中，保留一个即可")
            break

    # ── 6. Because/so 同句 ──
    for s in sentences:
        if re.search(r'\bbecause\b', s, re.I) and re.search(r'\bso\b', s, re.I):
            grammar_error_count += add_grammar_issue("⚠️ 句式错误：because 和 so 不能同时出现在同一句中，保留一个即可")
            break

    # ── 7. 缺少系动词 "It/This/That is..." ──
    missing_be = re.findall(r'\b(it|this|that)\s+(important|crucial|necessary|significant|essential|vital|good|bad|easy|difficult|hard|possible|impossible|likely|worthwhile|meaningful|reasonable)\s+(to|that|for)\b', essay, re.I)
    if missing_be:
        grammar_error_count += add_grammar_issue(f"⚠️ 缺少系动词：'{missing_be[0][0]} {missing_be[0][1]}' 前应有 is/was（如 It is important to...）", 1)

    # ── 8. "I am agree / I am like / I am think" ──
    am_verb = re.findall(r'\bI\s+am\s+(agree|like|think|believe|hope|want|need|know|understand|suppose|assume|consider|feel|doubt|realize|appreciate|recommend|suggest)\b', essay, re.I)
    if am_verb:
        grammar_error_count += add_grammar_issue(f"⚠️ '{am_verb[0][0]}' 用法错误：I am {am_verb[0][1]} → 应直接说 I {am_verb[0][1]}（am 后不能直接跟动词原形）", len(am_verb))

    # ── 9. "to + verb-ing / to + 过去式" ──
    to_gerund = re.findall(r'\bto\s+\w+ing\b', essay, re.I)
    to_past = re.findall(r'\bto\s+\w+ed\b', essay, re.I)
    to_errors = [m for m in to_gerund + to_past if not re.search(r'\b(to|into|onto|onto)\b', m, re.I)]
    if to_errors:
        grammar_error_count += add_grammar_issue(f"⚠️ 不定式用法错误 {len(to_errors)} 处（to 后应跟动词原形，不是 -ing 或 -ed）", len(to_errors))

    # ── 10. 动词搭配错误（enjoy/suggest/avoid + to do → 应为 doing）──
    gerund_verbs = re.findall(r'\b(enjoy|suggest|avoid|finish|practice|mind|consider|admit|deny|imagine|risk|resist|appreciate|delay|postpone|quit|give up|keep|keep on|carry on)\s+to\s+\w+\b', essay, re.I)
    if gerund_verbs:
        grammar_error_count += add_grammar_issue(f"⚠️ 动名词搭配错误 {len(gerund_verbs)} 处（{gerund_verbs[0][0]} 后应跟 doing，不是 to do）", len(gerund_verbs))

    # ── 11. 动词搭配错误（want/hope/expect + doing → 应为 to do）──
    infinitive_verbs = re.findall(r'\b(want|hope|expect|decide|plan|refuse|promise|agree|afford|manage|fail|tend|pretend|seem|appear|demand|desire|wish|would like|would love)\s+\w+ing\b', essay, re.I)
    if infinitive_verbs:
        grammar_error_count += add_grammar_issue(f"⚠️ 不定式搭配错误 {len(infinitive_verbs)} 处（{infinitive_verbs[0][0]} 后应跟 to do，不是 doing）", len(infinitive_verbs))

    # ── 12. 比较级错误：more better, more easier, most biggest ──
    double_comp = re.findall(r'\b(more|most)\s+\w+(er|est)\b', essay, re.I)
    if double_comp:
        grammar_error_count += add_grammar_issue(f"⚠️ 比较级形式错误 {len(double_comp)} 处（more/most 不要和 -er/-est 同时使用）", len(double_comp))

    # ── 13. "I very like" → 副词位置错误 ──
    very_verb = re.findall(r'\bI\s+very\s+(like|enjoy|love|hate|want|need|know|understand|appreciate|support|agree|believe|hope|wish)\b', essay, re.I)
    if very_verb:
        grammar_error_count += add_grammar_issue(f"⚠️ 副词位置错误：I very {very_verb[0][0]} → 应为 I {very_verb[0][0]} very much", len(very_verb))

    # ── 14. 句首代词格错误（Me/Him/Her/Them 作主语）──
    wrong_case = re.findall(r'\b(Me|Him|Her|Us|Them)\s+\w+\b', essay)
    if wrong_case:
        grammar_error_count += add_grammar_issue(f"⚠️ 代词格错误：句首 '{wrong_case[0][0]}' 应为主格（I/He/She/We/They）", len(wrong_case))

    # ── 15. 可数名词前缺限定词（粗略）──
    # "Government should..." → "The government should..."
    # "Society is..." → 不报（society 可抽象）
    bare_noun = re.findall(r'\b(Government|Society|Environment|Education|Technology|Economy|Health|Nature|Science)\s+(is|are|was|were|has|have|plays|plays|plays)\b', essay)
    if bare_noun:
        grammar_error_count += add_grammar_issue(f"⚠️ 冠词缺失：'{bare_noun[0][0]}' 前通常需要 the", 1)

    # ── 16. "a lots of" → 应为 a lot of ──
    lots = re.findall(r'\ba\s+lots\s+of\b', essay, re.I)
    if lots:
        grammar_error_count += add_grammar_issue(f"⚠️ 'a lots of' 拼写错误，应为 a lot of", len(lots))

    # ── 17. "many + 不可数名词" ──
    many_uncountable = re.findall(r'\bmany\s+(information|advice|knowledge|research|homework|evidence|progress|feedback|furniture|equipment|traffic|weather|scenery|news|staff|baggage|luggage|mail|money|music|work|fun|nature|space|time|energy|health|help|food|water|air|rain|snow|sunshine|darkness|happiness|beauty|education|employment|infrastructure|pollution|poverty|literature|poetry|fiction|hardware|software)\b', essay, re.I)
    if many_uncountable:
        grammar_error_count += add_grammar_issue(f"⚠️ 用量错误：'{many_uncountable[0][1]}' 是不可数名词，应用 much/a lot of 而不是 many", len(many_uncountable))

    # ── 18. There is/are + 复数/单数不匹配 ──
    there_is_plural = re.findall(r'\bthere\s+is\s+\w+\s+(and\s+)?\w+s\b', essay, re.I)
    if there_is_plural and 'there is a' not in essay.lower() and 'there is an' not in essay.lower() and 'there is the' not in essay.lower():
        grammar_error_count += add_grammar_issue("⚠️ There is/are 不匹配：复数名词前应用 there are", 1)

    # ── 19. 双重否定 ──
    double_neg = re.findall(r"\b(don't|doesn't|didn't|won't|can't|couldn't|wouldn't|shouldn't|never|no|not|nothing|nobody)\s+\w+\s+(nothing|nobody|nowhere|none)\b", essay, re.I)
    if double_neg:
        grammar_error_count += add_grammar_issue(f"⚠️ 双重否定错误：一句话中不要使用两个否定词", 1)

    # ── 20. "make sb. to do" ──
    make_to = re.findall(r'\b(make|makes|made|let|lets)\s+\w+\s+to\s+\w+\b', essay, re.I)
    if make_to:
        grammar_error_count += add_grammar_issue(f"⚠️ 使役动词用法：make/let 后应跟动词原形，不要加 to", 1)

    # ── 21. 缺少主语（句首直接是动词原形）──
    for s in sentences[:5]:
        s = s.strip()
        if s and re.match(r'^(Is|Are|Was|Were|Has|Have|Do|Does|Did)\s+\w+', s) and not s.endswith('?'):
            # "Is a important issue" → missing "It"
            first_word = s.split()[0] if s.split() else ''
            if first_word and first_word[0].isupper():
                grammar_error_count += add_grammar_issue(f"⚠️ 缺少主语：句首 '{s[:30]}...' 缺少主语 It/There", 1)
                break

    # ── 22. "can be able to" ── 冗余 ──
    can_able = re.findall(r'\bcan\s+be\s+able\s+to\b', essay, re.I)
    if can_able:
        grammar_error_count += add_grammar_issue("⚠️ 冗余表达：'can be able to' → 直接用 can 即可", 1)

    # ── 23. 时态混用检查 ──
    past_words = {'was','were','had','did','said','made','went','came','took','gave','got','found','knew',
                  'thought','brought','left','felt','kept','began','built','sold','told','meant','paid','sent',
                  'set','ran','saw','taught','wrote','led','became','held','grew','lost','spoke','stood','won',
                  'threw','woke','wore','understood','showed','believed','considered','continued','developed',
                  'increased','provided','reduced','created','changed','followed','allowed','required','produced',
                  'happened','appeared','achieved','described','decided','established','expressed','introduced',
                  'performed','suggested','needed','started','tried','looked','used','called','worked','wanted',
                  'asked','helped','played','seemed','expected','accepted','received','carried','remained',
                  'realized','represented','studied','formed','identified','encouraged','compared','designed',
                  'improved','prevented','reflected','reported','served','supported','adopted','applied'}
    present_3rd = {'plays','does','goes','has','says','makes','takes','comes','gives','gets','finds','knows',
                   'thinks','brings','leaves','feels','keeps','begins','builds','sells','tells','means','pays',
                   'sends','sets','lets','runs','sees','teaches','writes','leads','becomes','holds','grows',
                   'loses','draws','drives','drinks','stands','wins','wears','understands','believes','considers',
                   'continues','includes','develops','increases','provides','reduces','creates','changes','follows',
                   'allows','requires','produces','happens','appears','achieves','describes','decides','establishes',
                   'expresses','introduces','performs','suggests','affects','offers','needs','starts','tries','looks',
                   'uses','calls','works','wants','asks','helps','plays','seems','expects','accepts','receives',
                   'carries','remains','realizes','represents','studies','forms','identifies','encourages','compares',
                   'designs','improves','prevents','reflects','reports','serves','supports','adopts','applies'}
    low_essay = essay.lower()
    found_past = [w for w in past_words if re.search(rf'\b{w}\b', low_essay)]
    found_3rd = [w for w in present_3rd if re.search(rf'\b{w}\b', low_essay)]
    if len(found_past) >= 2 and len(found_3rd) >= 2:
        grammar_error_count += add_grammar_issue("⚠️ 时态混用：同时出现一般过去时和一般现在时第三人称单数", 1)

    # ── 24. 句子首字母大写 ──
    cap_errors = sum(1 for s in sentences if s and s[0].islower())
    if cap_errors:
        grammar_error_count += add_grammar_issue(f"⚠️ 句首字母未大写（{cap_errors} 处）", cap_errors)

    # ── 语法扣分 ──
    # 语法扣分：每个语法错误扣0.8分，上限7分
    grammar_deduction = min(grammar_error_count * 0.8, 7.0)
    deduction += grammar_deduction

    if grammar_issues:
        for g in grammar_issues[:6]:
            warnings.append(g)
    else:
        suggestions.append("✅ 语法基本正确，无明显错误")

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
