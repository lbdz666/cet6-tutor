"""
翻译批改 LLM 增强版 — 在规则评分基础上，调用 LLM 进行语义级深度评估
"""
import json, re
from src.agent.llm import LLM

EVAL_PROMPT = """你是一位经验丰富的大学英语六级（CET-6）翻译阅卷老师。请严格按照六级翻译评分标准，对学生的译文进行详细评分。

## 原文
{original}

## 学生译文
{translation}

## 六级翻译评分标准（满分15分）

### 信 — 忠实原文（权重40%）
- 是否完整传递了原文所有信息？
- 关键术语/专有名词翻译是否正确？
- 有无漏译、误译、过度发挥？

### 达 — 通顺地道（权重35%）
- 语法是否正确（时态、语态、主谓一致、冠词、介词）？
- 表达是否符合英语习惯？
- 句子衔接是否自然流畅？

### 雅 — 用词风格（权重25%）
- 词汇是否丰富、精准？
- 句式是否有变化（简单句/复合句搭配）？
- 语言风格是否正式得体？

## 输出要求
请严格以 **JSON 格式** 输出评分结果，不要包含任何其他文字。JSON 结构如下：
{{
  "total_score": <整数，1-15>,
  "band": "<分档名称，如：14分档 (13-15分)>",
  "dimensions": {{
    "faithfulness": {{
      "score": <整数，1-15>,
      "issues": [<字符串数组，具体扣分项>],
      "suggestions": [<字符串数组，改进建议>]
    }},
    "fluency": {{
      "score": <整数，1-15>,
      "issues": [<字符串数组>],
      "suggestions": [<字符串数组>]
    }},
    "style": {{
      "score": <整数，1-15>,
      "issues": [<字符串数组>],
      "suggestions": [<字符串数组>]
    }}
  }},
  "summary": "<一句话总体评价>",
  "key_errors": [<列出最严重的3-5个具体错误>]
}}

评分参考：
- 13-15分：优秀，信达雅全面达标
- 10-12分：良好，少量小错误
- 7-9分：及格，有明显不足
- 4-6分：较差，大量严重错误
- 1-3分：极差，基本未掌握翻译技能
"""


def evaluate_translation_llm(original: str, translation: str, llm: LLM = None) -> dict:
    """调用 LLM 进行翻译语义级评分"""
    if llm is None:
        llm = LLM()
    
    prompt = EVAL_PROMPT.format(original=original, translation=translation)
    
    try:
        result = llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )
        # 提取 JSON
        json_str = result.strip()
        # 处理 LLM 可能用 ```json ... ``` 包裹的情况
        if "```" in json_str:
            json_str = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str)
            json_str = json_str.group(1) if json_str else result
        # 清理 BOM
        json_str = json_str.strip().lstrip('\ufeff')
        
        data = json.loads(json_str)
        return data
    except Exception as e:
        return {
            "total_score": 0,
            "band": "评分失败",
            "dimensions": {},
            "summary": f"LLM 评分异常：{str(e)}",
            "key_errors": []
        }


def format_llm_report(llm_result: dict) -> str:
    """将 LLM 评分结果格式化为可读报告"""
    if not llm_result or llm_result.get("total_score") == 0:
        return llm_result.get("summary", "评分失败，请重试")
    
    lines = []
    lines.append("## 🤖 AI 深度评分（LLM 语义分析）")
    lines.append("")
    
    # 总分
    ts = llm_result.get("total_score", 0)
    band = llm_result.get("band", "")
    lines.append(f"**LLM 总分：{ts}/15**  {band}")
    lines.append("")
    
    # 分维度
    dims = llm_result.get("dimensions", {})
    if dims:
        lines.append("### 📊 各维度评分")
        for dk, dn in [("faithfulness", "信·忠实度"), ("fluency", "达·通顺度"), ("style", "雅·风格")]:
            d = dims.get(dk, {})
            if d:
                score = d.get("score", "?")
                lines.append(f"**{dn}：{score}/15**")
                issues = d.get("issues", [])
                if issues:
                    for iss in issues[:4]:
                        lines.append(f"  • ⚠️ {iss}")
                suggestions = d.get("suggestions", [])
                if suggestions:
                    for sug in suggestions[:2]:
                        lines.append(f"  • 💡 {sug}")
        lines.append("")
    
    # 总体评价
    summary = llm_result.get("summary", "")
    if summary:
        lines.append(f"**总体评价：** {summary}")
        lines.append("")
    
    # 关键错误
    key_errors = llm_result.get("key_errors", [])
    if key_errors:
        lines.append("### 🎯 最严重的错误")
        for i, err in enumerate(key_errors[:5], 1):
            lines.append(f"{i}. {err}")
    
    return "\n".join(lines)


# ── 工具注册信息 ──
TRANSLATION_EVAL_LLM_TOOL = {
    "name": "evaluate_translation_llm",
    "description": "四六级翻译批改（AI深度版）：调用AI对学生的翻译进行语义级评分，能发现规则引擎无法检测的语义错误、逻辑问题和不地道表达。",
    "parameters": {
        "type": "object",
        "properties": {
            "original": {"type": "string", "description": "中文原文"},
            "translation": {"type": "string", "description": "学生英文译文"}
        },
        "required": ["original", "translation"]
    }
}
