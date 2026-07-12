"""
作文批改 LLM 增强版 — 在规则评分基础上，调用 LLM 进行语义级深度评估
"""
import json, re
from src.agent.llm import LLM

ESSAY_EVAL_PROMPT = """你是一位经验丰富的大学英语四六级（CET-4/6）作文阅卷老师。请严格按照官方评分标准，对学生的作文进行详细评分。

## 作文题目
{level_label}考试作文

## 学生作文
{essay}

## 评分标准（满分15分）

### 内容切题（权重30%）
- 是否紧扣题目要求？
- 论点是否清晰、充分展开？
- 例证是否具体、有说服力？

### 结构连贯（权重30%）
- 段落层次是否分明？
- 逻辑是否清晰连贯？
- 连接词使用是否恰当？

### 语言质量（权重40%）
- 语法是否准确（时态、语态、主谓一致、冠词、介词）？
- 词汇是否丰富、搭配是否恰当？
- 句式是否有变化（简单句/复合句搭配）？

## 扣分点参考
- 语法错误（每个 -0.5 分）
- 中式英语（每个 -0.5 分）
- 拼写错误（每个 -0.5 分）
- 标点错误（每个 -0.3 分）
- 字数不足/超标（视程度 -1~3 分）
- 结构混乱/逻辑不清（-1~3 分）
- 内容偏题/空洞（-2~5 分）

## 输出要求
请严格以 **JSON 格式** 输出评分结果，不要包含任何其他文字。JSON 结构如下：
{{
  "total_score": <整数，1-15>,
  "band": "<分档名称，如：14分档 (13-15分)>",
  "dimensions": {{
    "content": {{
      "score": <整数，1-15>,
      "issues": [<字符串数组，具体扣分项>],
      "suggestions": [<字符串数组，改进建议>]
    }},
    "structure": {{
      "score": <整数，1-15>,
      "issues": [<字符串数组>],
      "suggestions": [<字符串数组>]
    }},
    "language": {{
      "score": <整数，1-15>,
      "issues": [<字符串数组>],
      "suggestions": [<字符串数组>]
    }}
  }},
  "summary": "<一句话总体评价>",
  "key_errors": [<列出最严重的3-5个具体错误，直接指出错误原文>]
}}

评分参考：
- 13-15分：优秀，切题表达清晰，语言错误极少
- 10-12分：良好，基本切题，有少量错误
- 7-9分：及格，有明显不足和较多错误
- 4-6分：较差，内容/语言问题严重
- 1-3分：极差，基本未掌握写作技能
"""


def check_essay_llm(essay: str, level: str = "cet6", llm: LLM = None) -> dict:
    """调用 LLM 进行作文语义级评分"""
    if llm is None:
        llm = LLM()

    level_label = "四级 CET-4" if level == "cet4" else "六级 CET-6"
    prompt = ESSAY_EVAL_PROMPT.format(level_label=level_label, essay=essay)

    try:
        result = llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500,
        )
        json_str = result.strip()
        if "```" in json_str:
            json_str = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str)
            json_str = json_str.group(1) if json_str else result
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


def format_essay_llm_report(llm_result: dict) -> str:
    """将 LLM 评分结果格式化为可读报告"""
    if not llm_result or llm_result.get("total_score") == 0:
        return llm_result.get("summary", "评分失败，请重试")

    lines = []
    lines.append("## 🤖 AI 深度评分（LLM 语义分析）")
    lines.append("")

    ts = llm_result.get("total_score", 0)
    band = llm_result.get("band", "")
    lines.append(f"**LLM 总分：{ts}/15**  {band}")
    lines.append("")

    dims = llm_result.get("dimensions", {})
    if dims:
        lines.append("### 📊 各维度评分")
        for dk, dn in [("content", "内容切题"), ("structure", "结构连贯"), ("language", "语言质量")]:
            d = dims.get(dk, {})
            if d:
                score = d.get("score", "?")
                lines.append(f"**{dn}：{score}/15**")
                for iss in d.get("issues", [])[:4]:
                    lines.append(f"  • ⚠️ {iss}")
                for sug in d.get("suggestions", [])[:2]:
                    lines.append(f"  • 💡 {sug}")
        lines.append("")

    summary = llm_result.get("summary", "")
    if summary:
        lines.append(f"**总体评价：** {summary}")
        lines.append("")

    key_errors = llm_result.get("key_errors", [])
    if key_errors:
        lines.append("### 🎯 最严重的错误")
        for i, err in enumerate(key_errors[:5], 1):
            lines.append(f"{i}. {err}")

    return "\n".join(lines)


# ── 工具注册信息 ──
ESSAY_CHECK_LLM_TOOL = {
    "name": "check_essay_llm",
    "description": "四六级作文批改（AI深度版）：调用AI对学生的作文进行语义级评分，能发现规则引擎无法检测的语义错误、逻辑问题和内容偏题。",
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
