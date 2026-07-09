"""
LLM API 封装 — 支持国内主流 API
"""

import os
import json
from pathlib import Path
from typing import Optional
from openai import OpenAI

# 自动加载 .env 文件
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_default_client() -> OpenAI:
    """
    获取 LLM 客户端。
    支持的环境变量:
      LLM_API_KEY  — API Key
      LLM_BASE_URL — API 地址
      LLM_MODEL    — 模型名
    """
    api_key = os.getenv("LLM_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url)


def get_default_model() -> str:
    return os.getenv("LLM_MODEL", "deepseek-chat")


class LLM:
    """大模型调用封装"""

    def __init__(self, 
                 client: Optional[OpenAI] = None,
                 model: Optional[str] = None):
        self.client = client or get_default_client()
        self.model = model or get_default_model()

    def chat(self, 
             messages: list[dict],
             temperature: float = 0.7,
             max_tokens: int = 2048) -> str:
        """对话补全"""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    def chat_with_tools(self,
                        messages: list[dict],
                        tools: list[dict],
                        temperature: float = 0.3) -> tuple[str, Optional[dict]]:
        """
        带工具的对话。
        返回 (content, tool_call)
        如果 LLM 调用了工具，tool_call 不为 None
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools if tools else None,
            temperature=temperature,
        )
        msg = resp.choices[0].message

        # LLM 选择调用工具
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            return "", {
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments)
            }

        return msg.content or "", None
