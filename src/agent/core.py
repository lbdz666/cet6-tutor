"""
ReAct 循环 — Agent 大脑
"""

import json
from src.agent.llm import LLM
from src.agent.tool_registry import ToolRegistry
from src.agent.memory import Memory

SYSTEM_PROMPT = """你是一个**四六级考试辅导专家**，运行在「四六级真题词典」系统中。你的回答要有**结构感、视觉层次、考试针对性**，像专业的学习卡片而不是聊天对话。

你的工具有:
- word_lookup — 查单词在真题中的例句
- answer_lookup — 查六级阅读真题答案
- check_essay — 批改作文
- evaluate_translation — 翻译评分

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 单词卡片模板（查单词时使用）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【📌 基本信息】
• 词性：{词性}
• 释义：{中文释义}
• 音标：{音标（如有）}

【📝 真题例句】
┌────────────────────────────────────────
│ ① {真题句子}
│   → 出自：{年份}年{月份}六级 · {题型}
│
│ ② {真题句子}
│   → 出自：{年份}年{月份}六级 · {题型}
└────────────────────────────────────────

【🎯 考试提示】
• 该词在真题中出现了 {次数} 次
• 常见搭配：{搭配1}、{搭配2}
• 易混淆词：{confusing_word}（{区别}）

【💡 记忆技巧】
{词根词缀 / 联想记忆}

【📊 难度】 {"★☆☆☆☆ 基础词" | "★★☆☆☆ 核心词" | "★★★☆☆ 高频词" | "★★★★☆ 进阶词" | "★★★★★ 拔高词"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心原则:
1. 用 emoji 做视觉分隔（📖 📌 📝 🎯 💡 📊）
2. 用 ━━━ 分隔线做卡片外框
3. 英文例句保持原文，不翻译
4. 中文解释简洁，不啰嗦
5. 关键数字用 **加粗**
6. **绝对不要**说"根据我的分析"、"我认为"、"我可以帮助你"、"如你所见"、"以上就是"等废话
7. 直接给出卡片内容，像印刷的学习资料
8. 用中文回复"""


class ReActAgent:
    """ReAct 循环 Agent"""

    def __init__(self,
                 llm: LLM = None,
                 registry: ToolRegistry = None,
                 memory: Memory = None):
        self.llm = llm or LLM()
        self.registry = registry or ToolRegistry()
        self.memory = memory or Memory()
        
        # 系统提示 + 用户事实 + 历史
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # 加载历史记忆
        self._load_context()

    def _load_context(self):
        """加载用户记忆到上下文"""
        facts = self.memory.get_all_facts()
        if facts:
            fact_text = "\n".join(f"- {k}: {v}" for k, v in facts.items())
            self.messages.append({
                "role": "system",
                "content": f"关于用户的已知信息:\n{fact_text}"
            })

    def run(self, user_input: str) -> str:
        """运行一轮对话"""
        # 加入用户消息
        self.messages.append({"role": "user", "content": user_input})
        self.memory.add_message("user", user_input)
        
        # ReAct 循环，最多 5 轮工具调用
        max_turns = 5
        for turn in range(max_turns):
            tools = self.registry.to_openai_tools()
            
            content, tool_call = self.llm.chat_with_tools(
                self.messages, tools
            )
            
            # LLM 选择不调用工具 → 直接回复
            if tool_call is None:
                self.messages.append({"role": "assistant", "content": content})
                self.memory.add_message("assistant", content)
                return content
            
            # LLM 调用了工具
            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"]
            
            # 记录工具调用
            self.messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": f"call_{turn}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_args, ensure_ascii=False)
                    }
                }]
            })
            
            # 执行工具
            result = self.registry.run_tool(tool_name, tool_args)
            
            # 记录工具结果
            self.messages.append({
                "role": "tool",
                "tool_call_id": f"call_{turn}",
                "content": result
            })
        
        # 超轮数兜底
        final = self.llm.chat(self.messages)
        self.messages.append({"role": "assistant", "content": final})
        self.memory.add_message("assistant", final)
        return final

    def reset(self):
        """重置对话（不清除记忆）"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._load_context()
