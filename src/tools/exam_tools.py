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
            # 接近达标，轻微扣分
            warnings.append(f"⚠️ 字数略少：{limits['label']}要求 {limits['min']}-{limits['max']} 词，当前 {word_count} 词，建议写到 {limits['ideal']} 词左右")
            deduction += 0.5
        else:
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

    # ── 3e. 语法检查（重点）────────────────────
    grammar_issues = []
    grammar_error_count = 0

    # 主谓不一致：we is, you is, they is, we was, they has
    sv_errors = []
    sv_errors += re.findall(r'\b(we|you|they)\s+is\b', essay, re.I)
    sv_errors += re.findall(r'\b(we|you|they)\s+was\b', essay, re.I)
    sv_errors += re.findall(r'\b(we|you|they)\s+has\b', essay, re.I)
    sv_errors += re.findall(r'\b(he|she|it)\s+are\b', essay, re.I)
    sv_errors += re.findall(r'\b(he|she|it)\s+were\b', essay, re.I)
    sv_errors += re.findall(r'\b(he|she|it)\s+have\b', essay, re.I)
    sv_errors += re.findall(r'\bI\s+(is|are|was|were)\b', essay, re.I)
    sv_errors += re.findall(r'\bmy\s+(self|friend|mother|father|brother|sister|teacher)\s+are\b', essay, re.I)
    sv_errors += re.findall(r'\b(the|a|an)\s+\w+\s+are\b', essay, re.I)  # the book are → 粗略

    if sv_errors:
        grammar_issues.append(f"⚠️ 主谓不一致 {len(sv_errors)} 处（如：{sv_errors[0][0]}...）")
        grammar_error_count += len(sv_errors)

    # 情态动词后跟原型：can + 过去式 / must + 过去式 等
    modal_errors = []
    modal_errors += re.findall(r'\b(can|could|will|would|shall|should|may|might|must)\s+\w+ed\b', essay, re.I)
    modal_errors += re.findall(r'\b(can|could|will|would|shall|should|may|might|must)\s+\w+ing\b', essay, re.I)
    # can + to do → 错误(can to go)
    modal_errors += re.findall(r'\b(can|could|will|would|shall|should|may|might|must)\s+to\s+\w+\b', essay, re.I)

    if modal_errors:
        grammar_issues.append(f"⚠️ 情态动词用法错误 {len(modal_errors)} 处（情态动词后应跟动词原形）")
        grammar_error_count += len(modal_errors)

    # 双重过去式：didn't + 过去式
    double_past = re.findall(r"\b(didn't|did not|doesn't|does not|don't|do not)\s+\w+ed\b", essay, re.I)
    if double_past:
        grammar_issues.append(f"⚠️ 否定句式错误 {len(double_past)} 处（didn't/doesn't/don't 后应跟动词原形）")
        grammar_error_count += len(double_past)

    # 非谓语动词作主语时缺ing
    # 检查句首动词作主语是否用了原型(应有ing)
    for s in sentences:
        s_stripped = s.strip()
        if s_stripped:
            first_word = s_stripped.split()[0] if s_stripped.split() else ""
            if first_word and re.match(r'^[a-z]+$', first_word) and first_word.endswith('t') and len(first_word) > 3:
                pass  # 粗略跳过

    # 检查有无明显时态混用（用精确动词匹配）
    past_verbs = set(re.findall(r'\b(was|were|had|did|said|made|went|came|took|gave|got|found|knew|thought|brought|left|felt|kept|began|built|sold|told|put|meant|paid|sent|set|let|ran|saw|taught|wrote|led|became|held|grew|lost|drew|drove|drank|arose|drew|spoke|stood|won|stole|threw|woke|wore|understood|showed|believed|considered|continued|included|developed|increased|provided|reduced|created|changed|followed|allowed|required|produced|happened|appeared|achieved|described|decided|established|expressed|introduced|performed|presented|suggested|affected|offered|needed|started|tried|looked|used|called|worked|wanted|asked|helped|played|seemed|expected|accepted|received|carried|remained|realized|covered|represented|studied|formed|based|identified|encouraged|compared|designed|improved|prevented|reflected|reported|served|supported|turned|varied|adopted|applied|defined|measured|noted|proposed|selected|supplied|trained|treated|admitted|appointed|arranged|assumed|attracted|awarded|chose|collected|communicated|completed|confirmed|connected|constructed|contained|controlled|convinced|corrected|coupled|crossed|damaged|declared|declined|defeated|defended|delivered|demanded|denied|depended|derived|deserved|destroyed|determined|developed|devoted|differed|directed|disappeared|discovered|discussed|displayed|distinguished|distributed|dominated|doubted|earned|edited|educated|elected|eliminated|employed|enabled|encountered|ended|engaged|enjoyed|ensured|entered|established|evaluated|evolved|exceeded|exchanged|excluded|exhibited|expanded|expected|experienced|explained|explored|expressed|extended|extracted|facilitated|failed|favored|feared|filled|financed|finished|fixed|forced|forecast|formed|formulated|founded|framed|fulfilled|functioned|funded|gained|generated|governed|graduated|guaranteed|guided|handled|harmed|helped|identified|ignored|illustrated|imagined|implemented|imported|imposed|impressed|improved|included|incorporated|increased|indicated|induced|influenced|informed|initiated|injured|inserted|inspected|inspired|instituted|insured|integrated|intended|intensified|interpreted|intervened|interviewed|introduced|investigated|invited|involved|isolated|issued|joined|judged|justified|killed|labeled|landed|lack|launched|learned|limited|linked|listed|located|maintained|managed|manipulated|manufactured|marked|measured|mentioned|minimized|monitored|motivated|mounted|multiplied|narrowed|neglected|negotiated|nominated|noted|noticed|numbered|obtained|occupied|offered|operated|organized|oriented|originated|outlined|overcame|owned|participated|perceived|permitted|persuaded|placed|planned|pointed|possessed|practiced|praised|predicted|preferred|prepared|prescribed|presented|preserved|prevented|proceeded|processed|produced|programmed|prohibited|projected|promoted|prompted|proposed|protected|proved|provided|published|purchased|pursued|qualified|questioned|raised|ranged|ranked|rated|reacted|realized|received|recognized|recommended|recorded|recovered|recruited|reduced|referred|reflected|reformed|regarded|registered|regulated|rejected|related|released|relied|relocated|remained|remembered|reminded|removed|renewed|repeated|replaced|reported|represented|reproduced|requested|required|researched|resembled|reserved|resided|resigned|resisted|resolved|resourced|responded|restored|restricted|resulted|retained|retired|returned|revealed|reviewed|revised|revolutionized|rewarded|risked|satisfied|saved|scanned|scheduled|screened|secured|selected|separated|served|settled|severed|shaped|shared|shifted|shocked|shouted|signaled|signified|simplified|simulated|situated|skilled|smoked|solved|sought|specified|stimulated|stored|strained|strategized|strengthened|stressed|structured|studied|submitted|subscribed|substituted|succeeded|suffered|suggested|summarized|supervised|supplied|supported|supposed|suppressed|surrounded|surveyed|survived|suspected|sustained|symbolized|targeted|tended|terminated|tested|totaled|traced|tracked|traded|trained|transferred|transformed|translated|transmitted|transported|treated|triggered|trusted|tutored|uncovered|undertaken|undertook|unified|united|updated|upgraded|upheld|utilized|validated|valued|varied|verified|violated|visualized|volunteered|weakened|widened|withdrew|withheld|witnessed|wondered|wrapped|yielded)\b', essay, re.I))
    has_past = len(past_verbs) >= 2
    # 第三人称单数现在时动词
    present_3rd_verbs = set(re.findall(r'\b(plays|does|goes|has|says|makes|takes|comes|gives|gets|finds|knows|thinks|brings|leaves|feels|keeps|begins|builds|sells|tells|puts|means|pays|sends|sets|lets|runs|sees|teaches|writes|leads|becomes|holds|grows|loses|draws|drives|drinks|stands|wins|steals|throws|wakes|wears|understands|shows|believes|considers|continues|includes|develops|increases|provides|reduces|creates|changes|follows|allows|requires|produces|happens|appears|achieves|describes|decides|establishes|expresses|introduces|performs|presents|suggests|affects|offers|needs|starts|tries|looks|uses|calls|works|wants|asks|helps|plays|seems|expects|accepts|receives|carries|remains|realizes|covers|represents|studies|forms|bases|identifies|encourages|compares|designs|improves|prevents|reflects|reports|serves|supports|turns|varies|adopts|applies|defines|measures|notes|proposes|selects|supplies|trains|treats)\b', essay, re.I))
    has_present_3rd = len(present_3rd_verbs) >= 2
    if has_past and has_present_3rd:
        grammar_issues.append("⚠️ 时态混用：同时出现一般过去时和一般现在时第三人称单数")
        grammar_error_count += 1

    # 单复数错误：this + 复数名词 / these + 单数名词
    plural_errors = re.findall(r'\bthis\s+\w+s\b', essay, re.I)
    if plural_errors:
        grammar_issues.append(f"⚠️ 单复数错误 {len(plural_errors)} 处（this 后应跟单数名词）")
        grammar_error_count += len(plural_errors)

    # 冠词缺失（粗略检查：important/significant/crucial/necessary + 单数名词前缺a/an）
    missing_article = re.findall(r'\b(is|are|was|were|becomes|become|remains|remain)\s+(important|significant|crucial|necessary|effective|useful|good|bad|big|small|major|key)\s+\w+\b', essay, re.I)
    if missing_article:
        grammar_issues.append(f"⚠️ 可能缺少冠词：单数可数名词前通常需要 a/an/the")
        grammar_error_count += len(missing_article)

    # 句子首字母大写
    cap_errors = 0
    for s in sentences:
        if s and s[0].islower():
            cap_errors += 1
    if cap_errors > 0:
        grammar_issues.append(f"⚠️ 句首字母未大写（{cap_errors} 处）")
        grammar_error_count += cap_errors

    # 常见中式英语/语法错误模式
    common_patterns = [
        (r'\bvery\s+(good|important|necessary)\b', '"very good/important" 可用 greatly/extremely/highly 替代'),
        (r'\bmore\s+and\s+more\b', '"more and more" 可用 increasingly 替代'),
        (r'\bwith\s+the\s+development\b', '"with the development" 模板化开头'),
        (r'\bas\s+we\s+all\s+know\b', '"as we all know" 老套表达'),
        (r'\bevery\s+coin\s+has\s+two\s+sides\b', '"every coin has two sides" 模板化表达'),
    ]
    pattern_matches = 0
    for pat, hint in common_patterns:
        if re.search(pat, essay, re.I):
            if hint not in grammar_issues:
                grammar_issues.append(f"⚠️ {hint}")
                pattern_matches += 1

    # 语法扣分：每个语法错误扣1分，最多扣6分
    grammar_deduction = min(grammar_error_count * 1.0, 6.0)
    deduction += grammar_deduction

    if grammar_issues:
        for g in grammar_issues[:5]:
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
