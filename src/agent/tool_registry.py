"""
工具注册表 — Agent 调用的所有工具
"""

from typing import Any, Callable


class Tool:
    def __init__(self, 
                 name: str,
                 description: str,
                 fn: Callable,
                 parameters: dict):
        self.name = name
        self.description = description
        self.fn = fn
        self.parameters = parameters  # JSON Schema

    def to_openai_tool(self) -> dict:
        """转为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def run(self, **kwargs) -> str:
        try:
            result = self.fn(**kwargs)
            return str(result)
        except Exception as e:
            return f"[工具错误] {e}"


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict]:
        return [t.to_openai_tool() for t in self._tools.values()]

    def run_tool(self, name: str, arguments: dict) -> str:
        tool = self.get(name)
        if not tool:
            return f"[错误] 未知工具: {name}"
        return tool.run(**arguments)
