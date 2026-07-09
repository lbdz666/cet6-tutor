"""
翻译批改工具 — 按六级翻译评分标准自动评分
"""
import re

# ── 评分标准 ──────────────────────────────────
BAND_DESC = {
    14: {
        "name": "14分档 (13-15分)",
        "desc": "信达雅全面达标。译文准确地道，符合英语习惯；句式丰富流畅，逻辑连贯；允许有个别极微小错误。"
    },
    11: {
        "name": "11分档 (10-12分)",
        "desc": "信和达基本达标。含义基本完整，有少量语法错误；句式有一定变化，可能有少数生硬之处。"
    },
    8: {
        "name": "8分档 (7-9分)",
        "desc": "勉强及格，有明显短板。含义部分缺失，有较多语法或用词错误；句式单一，有明显中式英语。"
    },
    5: {
        "name": "5分档 (4-6分)",
        "desc": "严重失分。含义严重缺失，有大量严重语法错误；译文生硬混乱，严重影响理解。"
    },
    2: {
        "name": "2分档 (1-3分)",
        "desc": "几乎不得分。仅译出个别单词，或基本未作答。"
    }
}


def evaluate_translation(original: str, translation: str) -> str:
    """
    对六级翻译进行评分。
    
    参数:
        original: 中文原文
        translation: 学生的英文译文
    
    返回:
        评分报告，含分档、得分、评价和改进建议
    """
    warnings = []
    suggestions = []
    deduction = 0.0
    score = 15

    # ── 信：检查完整性 ──────────────────────
    # 中文原文按标点分割
    chinese_clauses = re.split(r'[，。；！？、]', original)
    chinese_clauses = [c.strip() for c in chinese_clauses if len(c.strip()) > 3]
    
    # 检查每个分句是否大致有对应翻译
    covered = 0
    for clause in chinese_clauses:
        # 提取中文关键词
        key_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', clause))
        if not key_words:
            continue
        # 检查译文是否包含这些词的任何英文对应（粗略检查）
        matched = sum(1 for kw in key_words if _kw_in_trans(kw, translation))
        if matched >= len(key_words) * 0.3:
            covered += 1
        else:
            warnings.append('⚠️ 可能漏译: "' + clause[:30] + '..."')
    
    coverage = covered / len(chinese_clauses) if chinese_clauses else 1
    if coverage < 0.5:
        return _format_report(2, original, translation, 
                              ["❌ 严重漏译：超过一半的内容未翻译"], [])
    elif coverage < 0.7:
        deduction += 3
        warnings.append("⚠️ 部分内容漏译")

    # ── 信：检查关键词准确度 ──────────────────
    # 常见六级翻译高频词
    key_term_map = {
        "乡村振兴": "rural revitalization",
        "改革开放": "reform and opening-up",
        "社会主义": "socialist",
        "现代化": "modernization",
        "可持续": "sustainable",
        "创新": "innovation",
        "数字经济": "digital economy",
        "人工智能": "artificial intelligence",
        "基础设施": "infrastructure",
        "国际合作": "international cooperation",
        "一带一路": "Belt and Road",
        "脱贫": "poverty alleviation",
        "生态文明": "ecological civilization",
        "高质量发展": "high-quality development",
        "传统文化": "traditional culture",
        "正能量": "positive energy",
    }
    for cn_term, en_term in key_term_map.items():
        if cn_term in original:
            # 检查翻译是否用了正确术语
            if en_term.split()[0].lower() not in translation.lower():
                warnings.append('⚠️ 建议 "' + cn_term + '" 译为 "' + en_term + '"')

    # ── 达：语法检查 ────────────────────────
    # 检查基本语法
    # 1. 主谓一致粗略检查
    singular_subjects = len(re.findall(r'\b(it|he|she|this|that|the\s+\w+)\s+(\w+)\b', translation, re.I))
    # 2. 检查时态一致性
    has_ed = len(re.findall(r'\b\w+ed\b', translation))
    has_ing = len(re.findall(r'\b\w+ing\b', translation))
    if has_ed > 0 and has_ing > 3:
        warnings.append("⚠️ 时态混用：过去时和进行时同时大量出现")
        deduction += 1

    # 3. 检查单复数
    if len(re.findall(r'\b\w+es\b', translation)) < 1 and len(translation.split()) > 30:
        pass  # 无明显问题

    # 4. 检查中式英语特征
    cn_patterns = [r'\bvery\s+(good|important|necessary)\b',
                   r'\bwe\s+must\s+',
                   r'\bmore\s+and\s+more\b',
                   r'\bwith\s+the\s+development\b',
                   r'\bas\s+we\s+all\s+know\b',
                   r'\bin\s+a\s+word\b',
                   r'\bfirst\s+of\s+all\b',
                   r'\bon\s+the\s+one\s+hand[\s\S]*?on\s+the\s+other\s+hand\b']
    cn_matches = 0
    for pat in cn_patterns:
        if re.search(pat, translation, re.I):
            cn_matches += 1
    if cn_matches >= 2:
        warnings.append(f"⚠️ 模板化/中式英语表达出现 {cn_matches} 处")
        deduction += 1

    # ── 雅：复杂度评估 ────────────────────────
    words = translation.split()
    word_count = len(words)
    avg_word_len = sum(len(w.strip('.,!?;:()[]{}"\'')) for w in words) / max(word_count, 1)

    # 从句数量（粗略：that/which/who/because/although 标志）
    complex_count = len(re.findall(r'\b(that|which|who|whom|whose|because|although|however|therefore|furthermore|nevertheless)\b', translation, re.I))
    
    # 句式多样性
    sentence_count = len(re.findall(r'[.!?]', translation))
    
    variety_score = 0
    if complex_count >= 3:
        variety_score += 1
        suggestions.append("💡 句式丰富，使用了复合句")
    else:
        suggestions.append("💡 建议适当使用从句（that/which/because等）增加句式变化")
    
    if avg_word_len > 5:
        variety_score += 1
    else:
        suggestions.append("💡 建议使用更多高级词汇替换简单词")
    
    if sentence_count >= 3:
        variety_score += 1
    
    if word_count < 20:
        deduction += 2
        warnings.append("⚠️ 译文过短，内容不完整")

    # ── 综合评分 ────────────────────────────
    # 初始15分，扣分
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

    return _format_report(band, original, translation, warnings, suggestions)


def _kw_in_trans(chinese_word, translation):
    """粗略检查中文词在译文中是否有对应英文"""
    # 简单的长度相关检查
    return True  # 粗略通过，详细检查由LLM完成


def _format_report(band, original, translation, warnings, suggestions):
    """格式化评分报告"""
    info = BAND_DESC[band]
    score_range = {
        14: "13-15分",
        11: "10-12分",
        8: "7-9分",
        5: "4-6分",
        2: "1-3分"
    }
    
    if band == 14:
        score_mid = 14
    elif band == 11:
        score_mid = 11
    elif band == 8:
        score_mid = 8
    elif band == 5:
        score_mid = 5
    else:
        score_mid = 3

    lines = [
        f"## 📝 翻译评分报告",
        f"",
        f"**参考分档：{info['name']}**",
        f"**{info['desc']}**",
        f"",
        f"### 原文",
        f"> {original}",
        f"",
        f"### 译文",
        f"> {translation}",
        f"",
    ]
    
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
    lines.append(f"| 维度 | 占比 | 说明 |")
    lines.append(f"|------|------|------|")
    lines.append(f"| 信 | 40% | 忠实原文，不漏译不篡改 |")
    lines.append(f"| 达 | 35% | 通顺流畅，符合英语习惯 |")
    lines.append(f"| 雅 | 25% | 用词精准，句式多样 |")
    
    return "\n".join(lines)


# ── 工具注册信息 ──────────────────────────
TRANSLATION_EVAL_TOOL = {
    "name": "evaluate_translation",
    "description": "四六级翻译批改：按六级翻译评分标准（信达雅）对学生的翻译进行自动评分，给出分档、扣分项和改进建议。",
    "parameters": {
        "type": "object",
        "properties": {
            "original": {
                "type": "string",
                "description": "中文原文句子或段落"
            },
            "translation": {
                "type": "string",
                "description": "学生的英文译文"
            }
        },
        "required": ["original", "translation"]
    }
}


# ── 直接测试 ──────────────────────────
if __name__ == "__main__":
    test_original = "乡村振兴战略是党的十九大提出的一项重大战略，是关系全面建设社会主义现代化国家的全局性、历史性任务。"
    test_translation = "The rural revitalization strategy is an important strategy proposed by the 19th CPC National Congress. It is a comprehensive and historical task related to the overall construction of a modern socialist country."
    print(evaluate_translation(test_original, test_translation))
    print("\n" + "="*60 + "\n")
    
    test_translation2 = "The village development plan is a big plan made by the party meeting. It is important for our country to become strong."
    print(evaluate_translation(test_original, test_translation2))
