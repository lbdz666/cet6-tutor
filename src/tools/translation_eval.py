"""
翻译批改工具 — 六级翻译精准评分（v2 全面升级）
评分体系：信(40%) + 达(35%) + 雅(25%) = 满分15分
"""

import re

# ═══════════════════════════════════════════════
# 一、评分档位定义
# ═══════════════════════════════════════════════

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

# ═══════════════════════════════════════════════
# 二、术语词典（覆盖六级翻译高频主题）
# ═══════════════════════════════════════════════

KEY_TERMS = {
    # ── 政治/政策 ──
    "乡村振兴": "rural revitalization",
    "改革开放": "reform and opening-up",
    "社会主义": "socialist",
    "现代化": "modernization",
    "脱贫攻坚": "poverty alleviation",
    "一带一路": "Belt and Road",
    "伟大复兴": "great rejuvenation",
    "中国梦": "Chinese Dream",
    "全面小康": "moderately prosperous society",
    "共同富裕": "common prosperity",
    "高质量发展": "high-quality development",
    "文明": "civilization",
    "民族": "nation",
    "传统美德": "traditional virtues",
    "和谐社会": "harmonious society",
    # ── 经济/科技 ──
    "数字经济": "digital economy",
    "人工智能": "artificial intelligence",
    "创新": "innovation",
    "基础设施": "infrastructure",
    "可持续发展": "sustainable development",
    "一带一路": "Belt and Road",
    "电子商务": "e-commerce",
    "大数据": "big data",
    "航天": "space",
    "互联网": "internet",
    "5G": "5G",
    "新能源": "new energy",
    "制造业": "manufacturing",
    "高端": "high-end",
    "科技": "technology",
    "网络": "network",
    # ── 社会/民生 ──
    "老龄化": "aging",
    "养老保险": "endowment insurance",
    "医疗": "medical",
    "教育": "education",
    "就业": "employment",
    "城镇化": "urbanization",
    "社会保障": "social security",
    "公共服务": "public services",
    "志愿服务": "voluntary service",
    "脱贫": "poverty alleviation",
    "人均": "per capita",
    "可支配": "disposable",
    # ── 文化 ──
    "传统文化": "traditional culture",
    "非物质文化遗产": "intangible cultural heritage",
    "春节": "Spring Festival",
    "中秋节": "Mid-Autumn Festival",
    "端午节": "Dragon Boat Festival",
    "书法": "calligraphy",
    "成语": "idiom",
    "瓷器": "porcelain",
    "丝绸": "silk",
    "刺绣": "embroidery",
    "剪纸": "paper-cutting",
    "京剧": "Peking Opera",
    "中医": "traditional Chinese medicine",
    "故宫": "Forbidden City",
    "长城": "Great Wall",
    "园林": "garden",
    "节气": "solar term",
    "环保": "environmental protection",
    "生态文明": "ecological civilization",
    # ── 自然/地理 ──
    "黄河": "Yellow River",
    "长江": "Yangtze River",
    "高原": "plateau",
    "青藏铁路": "Qinghai-Tibet Railway",
    "湿地": "wetland",
    "森林": "forest",
    "生物多样性": "biodiversity",
    # ── 节日/习俗 ──
    "团圆": "reunion",
    "赏月": "admire the moon|enjoy the moon",
    "月饼": "mooncake|moon cake",
    "灯笼": "lantern",
    "团圆饭": "family reunion dinner",
    # ── 形容词/高频表达 ──
    "辉煌": "glorious",
    "悠久": "long-standing",
    "灿烂": "splendid",
    "独特": "unique",
    "丰富": "rich / abundant",
    "重要": "important / significant",
    "快速": "rapid / fast",
    "显著": "remarkable / significant",
    "广泛": "wide / extensive",
}

# 六级高频主题词归类（用于检测主题正确性）
THEME_WORDS = {
    "文化传统": ["传统", "文化", "节日", "习俗", "纪念", "庆祝", "历史", "遗产"],
    "经济发展": ["经济", "发展", "增长", "产业", "市场", "贸易", "投资", "GDP"],
    "科技创新": ["科技", "创新", "技术", "发明", "研发", "互联网", "智能", "数字"],
    "社会生活": ["生活", "人口", "城市", "社区", "服务", "保障", "健康", "教育"],
    "生态环保": ["环境", "生态", "保护", "绿色", "可持续", "污染", "气候", "自然"],
}

# ═══════════════════════════════════════════════
# 三、中文→英文词映射（用于完整性检测）
# ═══════════════════════════════════════════════

# 高频中文词 → 可能的英文对应词（部分匹配即可）
CN_EN_WORD_MAP = {
    "和": "and",
    "的": "",  # 跳过功能词
    "了": "",
    "是": "is|are|was|were|has been|means|represents",
    "在": "in|on|at|within|among",
    "有": "has|have|with|there|possess",
    "与": "and|with|as well as",
    "为": "as|for|to|in order to",
    "从": "from|since|through",
    "到": "to|until|reach|arrive",
    "由": "by|from|compose|consist",
    "对": "to|for|regarding",
    "以": "with|by|in order to|so as to",
    "上": "on|above|over|up",
    "中": "in|among|during|middle",
    "下": "under|below|down|following",
    "大": "big|large|great|major|huge",
    "小": "small|little|tiny|minor",
    "多": "many|much|multiple|numerous",
    "好": "good|great|excellent|well",
    "新": "new|modern|fresh|novel",
    "高": "high|tall|top|advanced",
    "长": "long|length|grow",
    "最": "most|best|-est",
    "能": "can|could|able|capable",
    "会": "will|shall|can|meeting",
    "要": "must|should|need|important",
    "可": "can|may|possible",
    "很": "very|quite|rather|extremely",
    "更": "more|further|-er",
    "也": "also|too|as well|either",
    "都": "all|both|every|each",
    "就": "then|just|already|even",
    "还": "still|yet|also|in addition",
    "已": "already|yet|have been",
    "不": "not|no|un-|in-|dis-",
    "没有": "no|not|without|lack",
    "被": "be|by|passive voice",
    "把": "",  # 无直接对应，通常是宾语前置
    "它": "it|its",
    "他们": "they|them|their",
    "这个": "this|the",
    "这些": "these|those",
    "每": "every|each|per",
    "年": "year|annual",
    "天": "day|daily",
    "人": "people|person|human|individual",
    "时": "time|when|period|era",
    "个": "",  # 量词，无直接对应
    "种": "kind|type|sort|variety",
    "些": "some|several|a few",
    "来": "come|bring|since(in time)",
    "去": "go|leave|past",
    "看": "see|look|watch|view",
    "说": "say|speak|tell|talk|express",
    "做": "do|make|conduct|perform",
    "用": "use|apply|utilize|with",
    "成": "become|form|achieve|complete",
    "变": "change|become|transform|shift",
    "增": "increase|grow|rise|raise",
    "减": "decrease|reduce|decline|drop",
    "超": "exceed|surpass|overtake|beyond",
    "建": "build|establish|construct|found",
    "发": "develop|issue|launch|publish",
    "展": "exhibit|display|show|expand",
    "提": "improve|raise|propose|suggest",
    "促": "promote|facilitate|boost|drive",
    "现": "appear|emerge|present|current",
    "开": "open|start|begin|initiate",
    "关": "close|shut|related|concern",
    "出": "out|produce|emerge|export",
    "回": "back|return|reply|response",
    "以": "to|in|by|with",  # 同义但有重复
    "使": "make|enable|cause|let",
    "让": "let|make|allow|enable",
    "给": "give|provide|offer|supply",
    "由于": "due to|because of|owing to|thanks to",
    "为了": "in order to|to|for|so as to",
    "所以": "so|therefore|thus|consequently|hence",
    "因为": "because|since|as|for",
    "但是": "but|however|yet|nevertheless|whereas",
    "虽然": "although|though|even though|while",
    "如果": "if|whether|should|suppose",
    "当": "when|while|as|during",
    "通过": "through|by|via|by means of",
    "随着": "with|along with|as",
    "之间": "between|among|in between",
    "之外": "besides|apart from|in addition to|beyond",
    "关于": "about|regarding|concerning|with respect to",
    "作为": "as|as a|serving as",
    "经过": "through|after|via|undergo",
    "包括": "include|comprise|consist of|contain",
    "成为": "become|turn into|grow into",
    "进行": "conduct|carry out|undertake|perform",
    "实现": "realize|achieve|fulfill|implement",
    "发展": "develop|grow|expand|advance",
    "提高": "improve|enhance|raise|increase|boost",
    "促进": "promote|facilitate|boost|foster",
    "加强": "strengthen|reinforce|enhance|consolidate",
    "推动": "promote|drive|push forward|propel",
    "保持": "maintain|keep|preserve|sustain",
    "支持": "support|back|uphold|advocate",
    "帮助": "help|assist|aid|support",
    "解决": "solve|resolve|address|tackle",
    "面临": "face|confront|encounter|be faced with",
    "提供": "provide|offer|supply|furnish",
    "表示": "show|indicate|express|represent|demonstrate",
    "认为": "think|believe|consider|hold|regard",
    "需要": "need|require|demand|calling for",
    "可能": "may|might|possible|likely|probably",
    "应该": "should|ought to|must|shall",
    "注重": "focus on|emphasize|pay attention to|stress",
    "强调": "emphasize|stress|highlight|underline",
    "位于": "located|situated|lie|stand",
    "产生": "produce|generate|create|give rise to",
    "形成": "form|shape|take shape|develop into",
    "逐渐": "gradually|progressively|steadily|increasingly",
    "不断": "constantly|continuously|unceasingly|relentlessly",
    "目前": "currently|at present|nowadays|now",
    "已经": "already|have been|has been",
    "以来": "since|for the past",
    "之一": "one of|among",
    "关系": "relation|relationship|connection",
    "影响": "influence|impact|affect|effect",
    "作用": "role|function|effect|action",
    "方面": "aspect|area|field|respect|dimension",
    "领域": "field|area|domain|realm",
    "方式": "way|method|means|approach|mode",
    "能力": "ability|capability|capacity|competence",
    "水平": "level|standard|quality",
    "数量": "quantity|amount|number|volume",
    "质量": "quality",
    "程度": "degree|extent|level",
    "范围": "range|scope|coverage|extent",
    "种类": "type|kind|category|variety",
    "特点": "feature|characteristic|trait|hallmark",
    "意义": "significance|meaning|importance|sense",
    "价值": "value|worth|merit",
    "地位": "status|position|standing|place",
    "成功": "success|succeed|successful",
    "经验": "experience",
    "情况": "situation|circumstance|condition|case",
    "任务": "task|mission|assignment",
    "目标": "goal|objective|target|aim",
    "计划": "plan|project|program|scheme",
    "制度": "system|institution|mechanism",
    "政策": "policy",
    "战略": "strategy",
    "改革": "reform",
}

# 介词短语检查
COMMON_PREPOSITIONS = ["in", "on", "at", "to", "for", "of", "with", "by", "from", "about", "as", "into", "through", "during", "without", "against", "between", "under", "over", "after", "before", "since", "until", "upon", "within", "beyond", "across", "along", "among", "toward", "despite"]

# 常见中式英语表达
CHINGLISH_PATTERNS = [
    (r'\bvery\s+(important|necessary|significant|essential|crucial)\b', 'very+强形容词堆砌，建议用 extremely/highly 或直接用形容词'),
    (r'\bwe\s+must\s+', '"we must"过于生硬，可改用 It is essential to / should'),
    (r'\bmore\s+and\s+more\b', '"more and more"非正式，建议用 increasingly / growing number of'),
    (r'\bwith\s+the\s+development\s+of\b', '"with the development of"模板化，尝试换用 as...grows / along with the progress of'),
    (r'\bas\s+we\s+all\s+know\b', '"as we all know"冗长，建议直接陈述'),
    (r'\bin\s+a\s+word\b', '"in a word"口语化，书面表达可用 In conclusion / To summarize'),
    (r'\bfirst\s+of\s+all\b', '"first of all"略显松散，可用 Firstly / To begin with'),
    (r'\bon\s+the\s+one\s+hand[\s\S]{0,50}?on\s+the\s+other\s+hand\b', '"on the one hand...on the other hand"冗长模板'),
    (r'\ball\s+in\s+all\b', '"all in all"口语化，建议用 Overall / In summary'),
    (r'\blast\s+but\s+not\s+least\b', '"last but not least"陈词滥调'),
    (r'\b(think|believe)\s+that\b', '注意：that从句一般可省略 "that"，使句子更简洁'),
    (r'\bthere\s+(is|are)\s+(many|a\s+lot\s+of|numerous)\b', '"there are many..."开头平淡，可调整语序'),
]

# 连接词/过渡词（正面项）
GOOD_CONNECTIVES = [
    "however", "therefore", "nevertheless", "furthermore", "moreover",
    "consequently", "in addition", "as a result", "on the contrary",
    "in contrast", "similarly", "likewise", "meanwhile", "subsequently",
    "not only", "both", "either", "neither", "although", "despite",
    "besides", "indeed", "specifically", "particularly", "notably",
]

# ═══════════════════════════════════════════════
# 四、核心评分逻辑
# ═══════════════════════════════════════════════

def _tokenize_cn(text):
    """中文分词（按字和常见双字词）"""
    words = set()
    # 双字词
    for i in range(len(text) - 1):
        if '\u4e00' <= text[i] <= '\u9fff' and '\u4e00' <= text[i + 1] <= '\u9fff':
            words.add(text[i:i+2])
    # 三字词
    for i in range(len(text) - 2):
        chunk = text[i:i+3]
        if all('\u4e00' <= c <= '\u9fff' for c in chunk):
            words.add(chunk)
    # 四字及以上
    for i in range(len(text) - 3):
        chunk = text[i:i+4]
        if all('\u4e00' <= c <= '\u9fff' for c in chunk):
            words.add(chunk)
    return words


def _extract_cn_phrases(text):
    """提取中文原文中的关键信息单元：数字、专有名词、引号内容"""
    info = []
    # 数字
    numbers = re.findall(r'[\d]+(?:[.]\d+)?(?:[万亿亿千百])?', text)
    for n in numbers:
        info.append(("number", n))
    # 引号内容
    quotes = re.findall(r'[""「」『』]([^""「」『』]+)[""「」『』]', text)
    for q in quotes:
        info.append(("quote", q))
    return info


def _check_number_accuracy(original, translation):
    """检查数字是否被准确翻译"""
    cn_numbers = re.findall(r'(\d+[\u4e00-\u9fff]*)', original)
    en_numbers = re.findall(r'(\d[\d,.%]*)', translation)
    if cn_numbers and not en_numbers:
        return [f"原文中有数字/数量（如「{cn_numbers[0]}」），译文未找到对应数字"]
    return []


def _check_keyword_accuracy(original, translation, issues, suggestions):
    """检查术语翻译准确性"""
    word_issues = []
    trans_lower = translation.lower()
    for cn_term, en_term in sorted(KEY_TERMS.items(), key=lambda x: -len(x[0])):
        if cn_term in original:
            en_words = re.split(r'\s*/\s*|\|', en_term)
            any_found = False
            for ew in en_words:
                ew = ew.strip()
                if not ew:
                    continue
                ew_parts = ew.lower().split()
                if all(part in trans_lower for part in ew_parts):
                    any_found = True
                    break
            if not any_found:
                word_issues.append((cn_term, en_term))
    
    if word_issues:
        issues.append(f"📕 术语翻译问题（共 {len(word_issues)} 处）：")
        for cn, en in word_issues[:8]:
            issues.append(f"  • 「{cn}」建议译为 {en}")
        if len(word_issues) > 8:
            issues.append(f"  ...及其他 {len(word_issues) - 8} 处")
    
    return len(word_issues)


def _check_cn_en_integrity(original, translation):
    """中文原文完整性检查 — 检测是否有明显漏译"""
    # 按句分割
    cn_sentences = re.split(r'[。！？；]', original)
    cn_sentences = [s.strip() for s in cn_sentences if len(s.strip()) >= 4]
    
    if not cn_sentences:
        return 1.0, []  # 原文太短，跳过
    
    # 把译文转为小写
    trans_lower = translation.lower()
    trans_words = set(trans_lower.split())
    
    covered_count = 0
    missing_details = []
    
    # 构建中文有意义词的集合：KEY_TERMS + 常见中文实词
    # 使用硬编码的中文实词表，避免任意子串
    MEANINGFUL_CN = {}
    for k in KEY_TERMS:
        MEANINGFUL_CN[k] = KEY_TERMS[k]
    for k, v in CN_EN_WORD_MAP.items():
        if len(k) >= 2 and v:
            MEANINGFUL_CN[k] = v
    
    for sent in cn_sentences:
        # 找出这句话中出现在词表中的词
        found_terms = {}
        for cn_word, en_pattern in sorted(MEANINGFUL_CN.items(), key=lambda x: -len(x[0])):
            if cn_word in sent:
                found_terms[cn_word] = en_pattern
        
        if not found_terms:
            # 句子中没有任何已知词，保守跳过
            covered_count += 1
            continue
        
        # 检查每个已知词在译文中是否有对应
        match_count = 0
        missing_here = []
        for cn_w, en_pat in found_terms.items():
            # 英文可能是多个选项（用 / 或 | 分隔）
            en_opts = re.split(r'\s*/\s*|\|', en_pat)
            any_match = False
            for opt in en_opts:
                opt = opt.strip()
                if not opt:
                    continue
                opt_parts = opt.lower().split()
                if all(p in trans_lower for p in opt_parts):
                    any_match = True
                    break
            if any_match:
                match_count += 1
            else:
                missing_here.append(cn_w)
        
        # 只有大部分词都匹配才算覆盖
        threshold = max(len(found_terms) * 0.35, 1)
        if match_count >= threshold:
            covered_count += 1
        elif found_terms:
            excerpt = sent[:35] + "..." if len(sent) > 35 else sent
            missing_details.append(f"  • 「{excerpt}」→ 其中「{'」「'.join(missing_here[:4])}」在译文中可能无对应")
    
    coverage = covered_count / len(cn_sentences) if cn_sentences else 1.0
    return coverage, missing_details


def _check_grammar(translation):
    """全面语法检查"""
    issues = []
    
    # 1. 冠词使用
    article_errors = []
    # 检查可数名词单数前是否缺冠词
    singular_nouns = re.findall(r'\b(a|an|the|this|that|my|your|his|her|its|our|their|each|every|no|one|another)\s+(\w+)\b', translation, re.I)
    # 检查明显缺冠词的情况：系动词/动词后紧跟单数名词
    missing_article_pattern = r'\b(is|are|was|were|has|have|become|as|called|known\s+as)\s+([a-z]+)\b'
    matches = re.findall(missing_article_pattern, translation, re.I)
    for m in matches[:3]:
        word = m[1]
        # 排除不可数名词、专有名词、形容词等情况
        if word.lower() not in ('it', 'this', 'that', 'here', 'there', 'also', 'now', 'one', 'more', 'most', 'some', 'many', 'much', 'all', 'both', 'each', 'every', 'part', 'able', 'willing', 'ready', 'likely', 'able', 'available', 'important', 'necessary'):
            article_errors.append(f"可能缺冠词：「{m[0]}」")
    if article_errors:
        for e in article_errors[:2]:
            issues.append(f"🔤 {e}")
    
    # 2. 介词搭配
    prep_issues = []
    # 常见的介词误用上下文
    prep_checks = [
        (r'\bdiscuss\s+about\b', '"discuss about" 冗余，直接用 discuss'),
        (r'\bemphasize\s+on\b', '"emphasize on" 应为 emphasize'),
        (r'\bimpact\s+(to|on)\s+', '"impact" 作动词时直接跟宾语，作名词用 "impact on"'),
        (r'\bprovide\s+(sb)\s+with\s+', '注意：provide sb with sth = 向某人提供某物'),
        (r'\bcomprise\s+of\b', '"comprise of" 应为 comprise / consist of'),
        (r'\bpay\s+attention\s+on\b', '"pay attention on" 应为 pay attention to'),
        (r'\bin\s+the\s+contrary\b', '"in the contrary" 应为 on the contrary'),
        (r'\bby\s+contrast\s+', '注意：by contrast 通常放句首'),
        (r'\bbenefit\s+for\b', '"benefit for" 应为 benefit from / benefit sb'),
        (r'\bdue\s+for\b', '"due for" 检查：是否应为 due to（由于）'),
    ]
    for pat, msg in prep_checks:
        if re.search(pat, translation, re.I):
            prep_issues.append(msg)
    if prep_issues:
        for p in prep_issues[:2]:
            issues.append(f"🔗 {p}")
    
    # 3. 时态一致性
    tense_issues = []
    has_past = bool(re.search(r'\b\w+ed\b', translation)) and not bool(re.search(r'\b(used|based|called|located|situated|known|regarded|considered|founded|established|developed|related)\b', translation, re.I))
    has_present_3rd = bool(re.search(r'\b\w+s\b', translation)) and not bool(re.search(r'\b\w+ss\b|\b\w+ous\b', translation, re.I))
    # 更精确的时态检测
    past_tensed = set(re.findall(r'\b(\w+ed)\b', translation.lower()))
    # 过滤掉形容词/分词
    past_tense_words = {w for w in past_tensed if w not in ('used', 'based', 'called', 'located', 'situated', 'known', 'regarded', 'considered', 'founded', 'established', 'developed', 'related', 'so-called', 'supposed', 'advanced', 'united', 'limited', 'mixed', 'aged', 'crowded')}
    
    if len(past_tense_words) >= 2 and len([w for w in translation.split() if w.lower().endswith('s') and not w.lower().endswith('ss')]) >= 3:
        # 同时有过去时和现在时，检测是否混用
        tense_issues.append(f"⚠️ 时态混用：检测到一般现在时和一般过去时混用（{', '.join(list(past_tense_words)[:3])}...），请保持全文时态统一")
    
    # 检查完成时
    has_perfect = bool(re.search(r'\b(has|have|had)\s+\w+ed\b', translation, re.I))
    if has_perfect and not re.search(r'\b(for|since|already|yet|recently|lately|ever|never)\b', translation, re.I):
        pass  # 完成时使用合理
    
    for t in tense_issues[:1]:
        issues.append(t)
    
    # 4. 主谓一致
    sv_issues = []
    # 检测第三人称单数主语+非三单动词
    sv_pairs = re.findall(r'\b(it|he|she|this|that|each|every|either|neither|one|the\s+\w+)\s+(\w+)\b', translation, re.I)
    for subj, verb in sv_pairs:
        vlow = verb.lower()
        if vlow.endswith('s') and not vlow.endswith('ss') and vlow not in ('has', 'does', 'goes', 'makes', 'takes', 'comes', 'gives', 'shows', 'means', 'refers', 'represents', 'indicates', 'suggests', 'proves', 'demonstrates'):
            # 可能是主语是单数但动词未加s
            pass  # 难以准确判断，暂不报错
    
    if sv_issues:
        for s in sv_issues[:1]:
            issues.append(s)
    
    # 5. 句子结构
    struct_issues = []
    # 残缺句（句子以从属连词开头但没有主句）
    fragments = re.findall(r'(?:^|[.!?]\s+)(Because|Although|Though|While|When|If|Since|Unless|Whereas)\s+[^.!?]{5,40}[.!?]', translation)
    # 这实际上可能是正确的从句开头，不做报警
    _ = fragments  # 占位，不误报
    
    # 逗号拼接句（两个独立句用逗号连接无连词）
    comma_splices = re.findall(r'[^.!?]{10,}[,]\s+[A-Z]\w+\s+\w+\s+\w+\s+\w+[,.]', translation)
    if comma_splices:
        struct_issues.append(f"⚠️ 逗号拼接句：两个独立句子用逗号连接，建议用句号或分号分隔，或加连接词（and/but/because等）")
    
    # 主语重复
    if re.search(r'\b(it|this|they)\b', translation, re.I) and re.search(r'[,;]\s*(it|this|they)\s+(is|are|was|were|has|have)\b', translation, re.I):
        struct_issues.append(f"💡 注意：从句或过渡后重复主语可能冗余（如 ', it is...'）")
    
    for s in struct_issues[:1]:
        issues.append(s)
    
    # 6. 词性/搭配
    lexical_issues = []
    # 常见搭配错误
    lexical_checks = [
        (r'\ba\s+[aeiou]\w+', '"a" 用于辅音音素前，"an" 用于元音音素前 — 注意统一'),
        (r'\bi\s+am\b', '"I am" 在正式写作中避免缩写'),
        (r'\bdont\b', '"don\'t" 在正式写作中应写全称 do not'),
        (r'\bwont\b', '"won\'t" 在正式写作中应写全称 will not'),
        (r'\bcant\b', '"can\'t" 在正式写作中应写全称 cannot'),
        (r'\bcouldnt\b', '"couldn\'t" → could not'),
        (r'\bwouldnt\b', '"wouldn\'t" → would not'),
        (r'\bits\s+not\b', '注意：its 是所有格，it\'s 是 it is 缩写'),
    ]
    for pat, msg in lexical_checks:
        if re.search(pat, translation, re.I):
            lexical_issues.append(msg)
    
    for l in lexical_issues[:2]:
        issues.append(l)
    
    return issues


def _check_completeness_score(original, translation, issues, suggestions):
    """信 - 完整性评分（满分40 → 归一化到分数贡献）"""
    coverage, missing_details = _check_cn_en_integrity(original, translation)
    
    if coverage < 0.3:
        issues.append("❌ 严重漏译：仅覆盖原文不到 30% 的内容")
        completeness_score = 5
    elif coverage < 0.5:
        issues.append("❌ 大量漏译：约一半内容未翻译")
        completeness_score = 12
    elif coverage < 0.7:
        issues.append(f"⚠️ 部分漏译：约 {int((1-coverage)*100)}% 的内容无对应翻译")
        completeness_score = 22
    elif coverage < 0.85:
        suggestions.append("💡 译文基本完整，但有个别地方可补充更准确对应")
        completeness_score = 30
    else:
        completeness_score = 37
    
    # 添加具体的漏译细节（最多3条）
    for detail in missing_details[:3]:
        issues.append(detail)
    
    return completeness_score


def _check_accuracy_score(original, translation, issues, suggestions):
    """信 - 准确性评分（满分60 → 归一化到分数贡献）"""
    deductions = 0
    
    # 1. 术语准确
    term_errors = _check_keyword_accuracy(original, translation, issues, suggestions)
    deductions += term_errors * 5
    
    # 2. 数字准确
    num_issues = _check_number_accuracy(original, translation)
    for n in num_issues:
        issues.append(f"🔢 {n}")
        deductions += 3
    
    # 3. 严重漏译惩罚：如果完整性极差，准确性也大幅扣分
    coverage, _ = _check_cn_en_integrity(original, translation)
    if coverage < 0.3:
        deductions += 25
    elif coverage < 0.5:
        deductions += 15
    elif coverage < 0.7:
        deductions += 5
    
    accuracy_score = max(60 - deductions, 5)
    
    return accuracy_score


def _check_fluency_score(translation, issues, suggestions):
    """达 - 通顺流畅度评分（满分100 → 归一化）"""
    fluency = 100
    issues_local = []
    
    # 1. 中式英语
    chinglish_count = 0
    for pattern, suggestion in CHINGLISH_PATTERNS:
        matches = re.findall(pattern, translation, re.I)
        if matches:
            chinglish_count += len(matches)
            issues_local.append(f"🇨🇳 中式英语表达：「{matches[0]}」— {suggestion}")
    
    fluency -= chinglish_count * 5
    
    # 2. 语法问题
    grammar_issues = _check_grammar(translation)
    fluency -= len(grammar_issues) * 4
    for g in grammar_issues:
        issues_local.append(g)
    
    # 3. 句子长度合理性
    sentences = re.split(r'[.!?]', translation)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if sentences:
        avg_sent_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sent_len < 6:
            issues_local.append("✂️ 句子过短（平均不到6词），建议合并短句增加连贯性")
            fluency -= 5
        elif avg_sent_len > 30:
            issues_local.append("📏 句子过长（平均超过30词），建议拆分长句")
            fluency -= 5
    
    # 4. 连接词丰富度
    connective_count = 0
    for conn in GOOD_CONNECTIVES:
        if re.search(r'\b' + conn + r'\b', translation, re.I):
            connective_count += 1
    if connective_count == 0 and len(sentences) >= 3:
        suggestions.append("💡 建议使用连接词（however/therefore/furthermore等）增强段落连贯性")
    
    # 5. 标点使用
    if '，' in translation:
        issues_local.append("🔣 发现中文标点「，」，应使用英文逗号「,」")
        fluency -= 2
    if '；' in translation:
        issues_local.append("🔣 发现中文标点「；」，应使用英文分号「;」")
        fluency -= 2
    if '（' in translation or '）' in translation:
        issues_local.append("🔣 发现中文括号，应使用英文括号")
        fluency -= 2
    
    # 6. 首字母大写
    for line in translation.strip().split('\n'):
        line = line.strip()
        if line and line[0].isalpha() and line[0].islower() and len(line) > 20:
            if not re.search(r'^[a-z]+[,;:]', line):  # 排除连接词开头
                pass  # 段落中首字母不大写是正常的
    
    # 7. 冠词扣分细化
    article_missing = re.findall(r'\b(is|was)\s+([a-z]+)\b', translation)
    for v, n in article_missing:
        if n.lower() not in ('it', 'called', 'known', 'located', 'situated', 'also', 'now', 'one', 'part'):
            # 很多情况不一定是缺冠词，只做提示
            if len(translation.split()) > 30:
                issues_local.append(f"💡 注意「{v} {n}」：如果是可数名词单数，前面可能缺冠词 a/an/the")
                break
    
    for item in issues_local[:8]:
        if item not in issues:
            issues.append(item)
    for item in issues_local[8:]:
        pass  # 限制显示数量
    
    return max(fluency, 15)


def _check_style_score(translation, issues, suggestions):
    """雅 - 用词与风格评分（满分100 → 归一化）"""
    style = 100
    
    words = translation.split()
    word_count = len(words)
    
    if word_count < 10:
        suggestions.append("📝 译文太短，无需评估用词风格")
        return 50
    
    # 1. 词汇丰富度（type-token ratio）
    unique_words = set(w.lower().strip('.,!?;:()[]{}"\'') for w in words)
    ttr = len(unique_words) / max(word_count, 1)
    if ttr < 0.40:
        suggestions.append("📝 词汇重复率偏高，尝试用同义词替换（如 important→significant/crucial）")
        style -= 8
    elif ttr > 0.70:
        style += 3  # 加分项
    
    # 2. 平均词长
    avg_len = sum(len(w.strip('.,!?;:()[]{}"\'')) for w in words) / max(word_count, 1)
    if avg_len < 4.0:
        suggestions.append("📝 用词偏简单短小，建议适当使用更精确的学术词汇（如 use→utilize/employ）")
        style -= 10
    elif avg_len > 6.5:
        suggestions.append('📝 词汇略偏复杂，注意不要为了"大词"牺牲准确性')
        style -= 5
    
    # 3. 从句/复杂结构
    clause_markers = len(re.findall(r'\b(that|which|who|whose|whom|where|when|because|although|though|while|unless|since|as|if|whether|despite|in spite of|due to|owing to|as a result of)\b', translation, re.I))
    if clause_markers >= 4:
        suggestions.append("📝 句式丰富，使用了多种从句结构 ✓")
        style += 5
    elif clause_markers <= 1 and word_count > 40:
        suggestions.append("📝 句式较单一，建议使用定语从句、状语从句等丰富结构")
        style -= 8
    
    # 4. 被动语态使用（正式文体加分）
    passive_count = len(re.findall(r'\b(is|are|was|were|been|being)\s+\w+ed\b', translation, re.I))
    if passive_count >= 2:
        style += 3
    
    # 5. 同义替换检测（ex：不使用重复的大词）
    # 检查是否有重复使用关键动词
    common_verbs = ["make", "take", "get", "have", "do", "go", "put"]
    overused = []
    for v in common_verbs:
        cnt = len(re.findall(r'\b' + v + r'\b', translation, re.I))
        if cnt >= 3:
            overused.append(v)
    if overused:
        suggestions.append(f"📝 基础动词「{'/'.join(overused)}」出现多次，可用更精准的动词替换")
        style -= 5
    
    return max(style, 10)


def _get_score_band(raw_score, max_score):
    """原始分数换算为1-15分制"""
    ratio = raw_score / max_score if max_score > 0 else 0
    return max(min(round(ratio * 15), 15), 1)


def evaluate_translation(original: str, translation: str) -> str:
    """
    对六级翻译进行精准评分（v2）。
    
    参数:
        original: 中文原文
        translation: 学生的英文译文
    
    返回:
        详细评分报告（Markdown格式）
    """
    issues = []
    suggestions = []
    
    # ─────────────────────────────────────────────
    # 维度一：信（40%）— 忠实度
    # ─────────────────────────────────────────────
    completeness_score = _check_completeness_score(original, translation, issues, suggestions)
    accuracy_score = _check_accuracy_score(original, translation, issues, suggestions)
    # 信综合 = 完整 × 0.4 + 准确 × 0.6
    fidelity_raw = completeness_score * 0.4 + accuracy_score * 0.6
    
    # ─────────────────────────────────────────────
    # 维度二：达（35%）— 通顺度
    # ─────────────────────────────────────────────
    fluency_score = _check_fluency_score(translation, issues, suggestions)
    
    # ─────────────────────────────────────────────
    # 维度三：雅（25%）— 风格
    # ─────────────────────────────────────────────
    style_score = _check_style_score(translation, issues, suggestions)
    
    # ─────────────────────────────────────────────
    # 综合评分
    # ─────────────────────────────────────────────
    # 各维度得分换算（百分制→15分制）
    fidelity_15 = _get_score_band(fidelity_raw, 50)
    fluency_15 = _get_score_band(fluency_score, 100)
    style_15 = _get_score_band(style_score, 100)
    
    # 加权总分
    total_15 = round(fidelity_15 * 0.40 + fluency_15 * 0.35 + style_15 * 0.25)
    total_15 = max(min(total_15, 15), 1)
    
    # 严重失分惩罚：如果忠实度（信）极低，总分不能太高
    if fidelity_15 <= 5:
        total_15 = min(total_15, 6)
    elif fidelity_15 <= 7:
        total_15 = min(total_15, 9)
    elif fidelity_15 <= 9:
        total_15 = min(total_15, 11)
    
    # 定档
    if total_15 >= 13:
        band = 14
        band_name = "14分档 (13-15分)"
    elif total_15 >= 10:
        band = 11
        band_name = "11分档 (10-12分)"
    elif total_15 >= 7:
        band = 8
        band_name = "8分档 (7-9分)"
    elif total_15 >= 4:
        band = 5
        band_name = "5分档 (4-6分)"
    else:
        band = 2
        band_name = "2分档 (1-3分)"
    
    band_info = BAND_DESC[band]["desc"]
    
    # ─────────────────────────────────────────────
    # 生成报告
    # ─────────────────────────────────────────────
    lines = []
    lines.append("## 📝 翻译评分报告")
    lines.append("")
    
    # 综合得分卡片
    lines.append("### 🏆 综合评分")
    lines.append(f"| 项目 | 结果 |")
    lines.append(f"|------|------|")
    lines.append(f"| **总分** | **{total_15} / 15 分** — {band_name} |")
    lines.append(f"| 分档描述 | {band_info} |")
    lines.append("")
    
    # 分维度得分
    lines.append("### 📊 各维度评分")
    lines.append("| 维度 | 权重 | 得分 | 评级 | 说明 |")
    lines.append("|------|:----:|:----:|:----:|------|")
    
    def _rating(score_15):
        if score_15 >= 13: return "🟢 优秀"
        elif score_15 >= 10: return "🔵 良好"
        elif score_15 >= 7: return "🟡 一般"
        elif score_15 >= 4: return "🟠 较差"
        else: return "🔴 极差"
    
    lines.append(f"| 信·忠实度 | 40% | {fidelity_15}/15 | {_rating(fidelity_15)} | 原文内容、术语、数字的翻译准确性 |")
    lines.append(f"| 达·通顺度 | 35% | {fluency_15}/15 | {_rating(fluency_15)} | 语法正确性、地道程度、衔接连贯 |")
    lines.append(f"| 雅·风格 | 25% | {style_15}/15 | {_rating(style_15)} | 词汇丰富度、句式多样性、书面语程度 |")
    lines.append("")
    
    # 原文与译文
    lines.append("### 📄 原文与译文对比")
    lines.append("> **原文：** " + original)
    lines.append(">")
    lines.append("> **译文：** " + translation)
    lines.append("")
    
    # 问题与扣分项
    if issues:
        lines.append("### ⚠️ 问题与扣分项")
        for i, w in enumerate(issues, 1):
            lines.append(f"{i}. {w}")
        lines.append("")
    
    # 改进建议
    if suggestions:
        lines.append("### 💡 改进建议")
        seen = set()
        for s in suggestions:
            if s not in seen:
                lines.append(f"- {s}")
                seen.add(s)
        lines.append("")
    
    # 评分标准
    lines.append("---")
    lines.append("")
    lines.append("### 📋 六级翻译评分标准")
    lines.append("| 维度 | 占比 | 具体内容 |")
    lines.append("|------|:----:|----------|")
    lines.append("| **信** — 忠实原文 | 40% | 不漏译、不篡改、术语准确、数字/专名正确 |")
    lines.append("| **达** — 通顺地道 | 35% | 语法正确、符合英语习惯、搭配恰当、衔接自然 |")
    lines.append("| **雅** — 风格优美 | 25% | 用词丰富精准、句式多样有变化、书面语正式程度 |")
    lines.append("")
    lines.append("> 💬 **提示：** 满分15分，9分以上为及格线。六级翻译要求180-200词段落翻译，内容涵盖中国社会、历史、文化、经济等。")
    
    return "\n".join(lines)


# ── 工具注册信息 ──
TRANSLATION_EVAL_TOOL = {
    "name": "evaluate_translation",
    "description": "四六级翻译批改（v2精准版）：按六级翻译评分标准（信40%+达35%+雅25%），对学生的翻译自动评分，给出分项得分、详细扣分项和改进建议。",
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


# ── 测试 ──
if __name__ == "__main__":
    print("=" * 70)
    print("测试1: 优秀译文")
    print("=" * 70)
    test1_orig = "乡村振兴战略是党的十九大提出的一项重大战略，是关系全面建设社会主义现代化国家的全局性、历史性任务。"
    test1_trans = "The rural revitalization strategy is an important strategy proposed by the 19th CPC National Congress. It is a comprehensive and historical task related to the overall construction of a modern socialist country."
    print(evaluate_translation(test1_orig, test1_trans))
    
    print("\n\n" + "=" * 70)
    print("测试2: 较差译文")
    print("=" * 70)
    test2_trans = "The village development plan is a big plan made by the party meeting. It is important for our country to become strong."
    print(evaluate_translation(test1_orig, test2_trans))
    
    print("\n\n" + "=" * 70)
    print("测试3: 中档译文")
    print("=" * 70)
    test3_orig = "人工智能的快速发展正在深刻改变人们的生活和工作方式。它不仅提高了生产效率，还为医疗、教育等领域带来了新的机遇。"
    test3_trans = "The rapid development of artificial intelligence is profoundly changing people's way of life and work. It not only improves production efficiency, but also brings new opportunities to fields such as healthcare and education."
    print(evaluate_translation(test3_orig, test3_trans))
