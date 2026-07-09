#!/usr/bin/env python3
"""
四六级真题词典 — 启动入口

用法:
  # 启动 Web 界面（推荐）
  python3 main.py

  # CLI 交互模式
  python3 main.py --cli

  # 单次查询
  python3 main.py --query "abandon 在真题中的用法"
"""

import sys
import os

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    args = sys.argv[1:]
    
    if "--cli" in args:
        _cli_mode()
    elif "--query" in args:
        idx = args.index("--query")
        query = " ".join(args[idx + 1:])
        _single_query(query)
    else:
        _web_mode()


def _web_mode():
    """启动 Web 界面"""
    print("🌐 启动 Web 界面...")
    from src.ui.app import launch
    share = "--share" in sys.argv
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
    launch(share=share, port=port)


def _cli_mode():
    """CLI 交互模式"""
    from src.agent.core import ReActAgent
    from src.agent.tool_registry import ToolRegistry, Tool
    from src.tools.word_lookup import word_lookup, WORD_LOOKUP_TOOL
    from src.tools.exam_tools import check_essay, ESSAY_CHECK_TOOL
    from src.tools.answer_lookup import format_exam_answers, ANSWER_LOOKUP_TOOL
    
    registry = ToolRegistry()
    registry.register(Tool(
        name=WORD_LOOKUP_TOOL["name"],
        description=WORD_LOOKUP_TOOL["description"],
        fn=word_lookup,
        parameters=WORD_LOOKUP_TOOL["parameters"]
    ))
    registry.register(Tool(
        name=ESSAY_CHECK_TOOL["name"],
        description=ESSAY_CHECK_TOOL["description"],
        fn=check_essay,
        parameters=ESSAY_CHECK_TOOL["parameters"]
    ))
    registry.register(Tool(
        name=ANSWER_LOOKUP_TOOL["name"],
        description=ANSWER_LOOKUP_TOOL["description"],
        fn=format_exam_answers,
        parameters=ANSWER_LOOKUP_TOOL["parameters"]
    ))
    
    agent = ReActAgent(registry=registry)
    
    print("📖 四六级真题词典 (CLI 模式)")
    print("输入问题，输入 q 退出\n")
    
    while True:
        try:
            user_input = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if not user_input:
            continue
        if user_input.lower() in ("q", "quit", "exit"):
            break
        
        print(agent.run(user_input))
        print()


def _single_query(query: str):
    """单次查询"""
    from src.agent.core import ReActAgent
    from src.agent.tool_registry import ToolRegistry, Tool
    from src.tools.word_lookup import word_lookup, WORD_LOOKUP_TOOL
    from src.tools.exam_tools import check_essay, ESSAY_CHECK_TOOL
    from src.tools.answer_lookup import format_exam_answers, ANSWER_LOOKUP_TOOL
    
    registry = ToolRegistry()
    registry.register(Tool(
        name=WORD_LOOKUP_TOOL["name"],
        description=WORD_LOOKUP_TOOL["description"],
        fn=word_lookup,
        parameters=WORD_LOOKUP_TOOL["parameters"]
    ))
    registry.register(Tool(
        name=ANSWER_LOOKUP_TOOL["name"],
        description=ANSWER_LOOKUP_TOOL["description"],
        fn=format_exam_answers,
        parameters=ANSWER_LOOKUP_TOOL["parameters"]
    ))
    registry.register(Tool(
        name=ESSAY_CHECK_TOOL["name"],
        description=ESSAY_CHECK_TOOL["description"],
        fn=check_essay,
        parameters=ESSAY_CHECK_TOOL["parameters"]
    ))
    
    agent = ReActAgent(registry=registry)
    result = agent.run(query)
    print(result)


if __name__ == "__main__":
    main()
