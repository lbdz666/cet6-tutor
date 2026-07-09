"""
ReAct 循环 — Agent 大脑
"""

import json
from src.agent.llm import LLM
from src.agent.tool_registry import ToolRegistry
from src.agent.memory import Memory

SYSTEM_PROMPT = """你是一个四六级真题词典，帮助大学生备考英语四六级考试。

你能做的是:
1. 查单词 — 在历年真题中查找单词，显示它在真题句子中的用法
2. 批改作文 — 检查作文并给出建议
3. 翻译批改 — 按六级翻译评分标准（信达雅）对翻译进行评分
4. 回答英语学习问题 — 语法、词汇、阅读技巧等
5. 推荐学习计划

回复要求:
- 用中文回复，英文例句保持原文
- 回答简洁、实用，直接给答案
- 如果需要查单词，使用 word_lookup 工具
- 如果需要批改翻译，使用 evaluate_translation 工具（需要提供中文原文和英文译文）
- 不确定时实事求是，不编造"""


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
