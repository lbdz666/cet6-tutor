"""
Gradio Web 界面 — 四六级真题词典
"""
import gradio as gr
import os
from src.agent.core import ReActAgent
from src.agent.tool_registry import ToolRegistry, Tool
from src.tools.word_lookup import word_lookup, WORD_LOOKUP_TOOL
from src.tools.exam_tools import check_essay, ESSAY_CHECK_TOOL
from src.tools.translation_eval import evaluate_translation, TRANSLATION_EVAL_TOOL


def build_agent() -> ReActAgent:
    """构建带工具的 Agent"""
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
        name=TRANSLATION_EVAL_TOOL["name"],
        description=TRANSLATION_EVAL_TOOL["description"],
        fn=evaluate_translation,
        parameters=TRANSLATION_EVAL_TOOL["parameters"]
    ))
    
    return ReActAgent(registry=registry)


def create_ui():
    """创建 Gradio 界面"""
    agent = build_agent()

    # ── AI 聊天 ─────────────────────────────
    def chat_fn(message, history):
        response = agent.run(message)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        return "", history

    def clear_fn():
        agent.reset()
        return [], ""

    # ── 翻译批改 ─────────────────────────────
    def grade_translation(original, translation):
        if not original or not original.strip():
            return "请填写中文原文"
        if not translation or not translation.strip():
            return "请填写英文译文"
        return evaluate_translation(original.strip(), translation.strip())

    def grade_example(example_name):
        examples = {
            "乡村振兴": {
                "original": "乡村振兴战略是党的十九大提出的一项重大战略，是关系全面建设社会主义现代化国家的全局性、历史性任务。",
                "translation": "The rural revitalization strategy is an important strategy proposed by the 19th CPC National Congress. It is a comprehensive and historical task related to the overall construction of a modern socialist country."
            },
            "中档译文": {
                "original": "乡村振兴战略是党的十九大提出的一项重大战略，是关系全面建设社会主义现代化国家的全局性、历史性任务。",
                "translation": "The village development plan is a big plan made by the party meeting. It is important for our country to become strong."
            },
            "人工智能": {
                "original": "人工智能的快速发展正在深刻改变人们的生活和工作方式。它不仅提高了生产效率，还为医疗、教育等领域带来了新的机遇。",
                "translation": "The rapid development of artificial intelligence is profoundly changing people's way of life and work. It not only improves production efficiency, but also brings new opportunities to fields such as healthcare and education."
            }
        }
        ex = examples.get(example_name)
        if ex:
            return ex["original"], ex["translation"]
        return "", ""

    with gr.Blocks(title="四六级真题词典") as demo:
        gr.Markdown("""
        # 📖 四六级真题词典
        
        收录 2016~2025 年四六级真题，支持：
        - 🔍 **查单词** — 在十年真题中查找单词的用法和例句
        - ✍️ **作文批改** / **翻译批改** — AI 自动评分
        - 💡 **学习建议** — 语法、阅读、翻译等问题答疑
        """)

        with gr.Tabs():
            with gr.Tab("💬 AI 问答"):
                chatbot = gr.Chatbot(height=450)
                msg = gr.Textbox(
                    placeholder="输入你的问题，例如：查一下 decline 在真题中的用法",
                    label="你的问题"
                )
                with gr.Row():
                    clear_btn = gr.Button("🗑️ 清空对话")
                
                gr.Examples(
                    examples=[
                        "查一下 decline 在真题中的用法",
                        "帮我检查这篇作文：Nowadays, more and more people believe that...",
                        "帮我看一下翻译：原文'人工智能正在改变世界。' 译文'AI is changing the world.'",
                        "environment 这个词在六级真题中怎么用的",
                    ],
                    inputs=msg,
                    label="点一下试试"
                )
                
                msg.submit(chat_fn, [msg, chatbot], [msg, chatbot])
                clear_btn.click(clear_fn, None, [chatbot, msg])

            with gr.Tab("📝 翻译批改"):
                gr.Markdown("""
                ### 六级翻译评分标准
                
                按 **信达雅** 三方面评分，满分15分，分五档。
                """)
                
                with gr.Row():
                    with gr.Column():
                        original_input = gr.Textbox(
                            label="中文原文",
                            placeholder="粘贴中文原文句子或段落",
                            lines=5
                        )
                    with gr.Column():
                        translation_input = gr.Textbox(
                            label="你的英文译文",
                            placeholder="粘贴你的英文译文",
                            lines=5
                        )
                
                with gr.Row():
                    grade_btn = gr.Button("📊 开始评分", variant="primary", size="lg")
                    clear_grade_btn = gr.Button("🗑️ 清空", size="lg")
                
                grade_output = gr.Markdown(label="评分结果")
                
                gr.Markdown("##### 试一个例子")
                with gr.Row():
                    example_btn1 = gr.Button("🌾 乡村振兴")
                    example_btn2 = gr.Button("📉 中档译文对比")
                    example_btn3 = gr.Button("🤖 人工智能")
                
                grade_btn.click(grade_translation, [original_input, translation_input], grade_output)
                clear_grade_btn.click(lambda: ("", "", ""), None, [original_input, translation_input, grade_output])
                
                example_btn1.click(
                    lambda: grade_example("乡村振兴"), None, [original_input, translation_input]
                )
                example_btn2.click(
                    lambda: grade_example("中档译文"), None, [original_input, translation_input]
                )
                example_btn3.click(
                    lambda: grade_example("人工智能"), None, [original_input, translation_input]
                )

    return demo


def launch(share: bool = False, port: int = 0):
    """启动 Web 界面"""
    demo = create_ui()
    actual_port = port or int(os.environ.get("PORT", 7860))
    demo.launch(share=share, server_port=actual_port, server_name="0.0.0.0")
