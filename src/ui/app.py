"""
Gradio Web 界面 — 四六级真题词典（优化版 v2）
"""
import gradio as gr
import os
from src.agent.core import ReActAgent
from src.agent.tool_registry import ToolRegistry, Tool
from src.tools.word_lookup import word_lookup, WORD_LOOKUP_TOOL
from src.tools.exam_tools import check_essay, ESSAY_CHECK_TOOL
from src.tools.translation_eval import evaluate_translation, TRANSLATION_EVAL_TOOL
from src.tools.translation_eval_llm import evaluate_translation_llm, format_llm_report, TRANSLATION_EVAL_LLM_TOOL
from src.tools.translation_lookup import get_translation, TRANSLATION_LOOKUP_TOOL
from src.tools.answer_lookup import format_exam_answers, list_available_exams, ANSWER_LOOKUP_TOOL

# ── 全局 CSS ─────────────────────────────
CUSTOM_CSS = """
.gradio-container { max-width: 960px !important; margin: 0 auto; }
h1 { font-size: 1.8rem !important; margin-bottom: 0.2rem !important; }
.tagline { color: #666; font-size: 0.95rem; margin-bottom: 1.2rem; }
.result-box {
    border-left: 4px solid #4f86c6; padding: 0.8rem 1rem;
    background: #f0f4ff !important; border-radius: 0 8px 8px 0;
    min-height: 80px;
}
.result-box, .result-box p, .result-box div, .result-box span,
.result-box *, .markdown-output, .markdown-output p, .markdown-output div {
    color: #1a1a2e !important;
}
button[role="tab"] { font-size: 0.95rem !important; padding: 8px 16px !important; }
button[role="tab"][aria-selected="true"] { border-bottom: 2px solid #4f86c6 !important; }
"""


def build_agent() -> ReActAgent:
    registry = ToolRegistry()
    registry.register(Tool(name=WORD_LOOKUP_TOOL["name"], description=WORD_LOOKUP_TOOL["description"], fn=word_lookup, parameters=WORD_LOOKUP_TOOL["parameters"]))
    registry.register(Tool(name=ESSAY_CHECK_TOOL["name"], description=ESSAY_CHECK_TOOL["description"], fn=check_essay, parameters=ESSAY_CHECK_TOOL["parameters"]))
    registry.register(Tool(name=TRANSLATION_EVAL_TOOL["name"], description=TRANSLATION_EVAL_TOOL["description"], fn=evaluate_translation, parameters=TRANSLATION_EVAL_TOOL["parameters"]))
    registry.register(Tool(name=ANSWER_LOOKUP_TOOL["name"], description=ANSWER_LOOKUP_TOOL["description"], fn=format_exam_answers, parameters=ANSWER_LOOKUP_TOOL["parameters"]))
    registry.register(Tool(name=TRANSLATION_EVAL_LLM_TOOL["name"], description=TRANSLATION_EVAL_LLM_TOOL["description"], fn=evaluate_translation_llm, parameters=TRANSLATION_EVAL_LLM_TOOL["parameters"]))
    registry.register(Tool(name=TRANSLATION_LOOKUP_TOOL["name"], description=TRANSLATION_LOOKUP_TOOL["description"], fn=get_translation, parameters=TRANSLATION_LOOKUP_TOOL["parameters"]))
    return ReActAgent(registry=registry)


def create_ui():
    agent = build_agent()

    # ── AI 问答 ─────────────────────────────
    def chat_fn(message, history):
        if not message or not message.strip():
            return "", history
        response = agent.run(message)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        return "", history

    def clear_fn():
        agent.reset()
        return [], ""

    # ── 作文批改 ────────────────────────────
    def grade_essay(essay, level):
        if not essay or not essay.strip():
            return "请粘贴你的作文"
        return check_essay(essay.strip(), level)

    # ── 翻译批改 ─────────────────────────────
    def grade_translation(original, translation):
        if not original or not original.strip():
            return "请填写中文原文"
        if not translation or not translation.strip():
            return "请填写英文译文"
        # 规则评分（快速）
        rule_result = evaluate_translation(original.strip(), translation.strip())
        # LLM 深度评分（语义级）
        try:
            llm_result = evaluate_translation_llm(original.strip(), translation.strip())
            llm_report = format_llm_report(llm_result)
            return rule_result + "\n\n" + llm_report
        except Exception as e:
            return rule_result + f"\n\n⚠️ AI 深度评分暂不可用（{str(e)}），以上为规则评分结果。"

    def grade_example(example_name):
        examples = {
            "乡村振兴": {"original": "乡村振兴战略是党的十九大提出的一项重大战略，是关系全面建设社会主义现代化国家的全局性、历史性任务。", "translation": "The rural revitalization strategy is an important strategy proposed by the 19th CPC National Congress. It is a comprehensive and historical task related to the overall construction of a modern socialist country."},
            "中档译文": {"original": "乡村振兴战略是党的十九大提出的一项重大战略，是关系全面建设社会主义现代化国家的全局性、历史性任务。", "translation": "The village development plan is a big plan made by the party meeting. It is important for our country to become strong."},
            "人工智能": {"original": "人工智能的快速发展正在深刻改变人们的生活和工作方式。它不仅提高了生产效率，还为医疗、教育等领域带来了新的机遇。", "translation": "The rapid development of artificial intelligence is profoundly changing people's way of life and work. It not only improves production efficiency, but also brings new opportunities to fields such as healthcare and education."}
        }
        ex = examples.get(example_name)
        if ex:
            return ex["original"], ex["translation"]
        return "", ""

    # ── 构建界面 ─────────────────────────────
    with gr.Blocks(title="四六级真题词典") as demo:
        gr.Markdown("""
        # 📖 四六级真题词典
        <div class="tagline">收录 2016~2025 年四六级真题 · 查单词 · 改作文 · 对答案</div>
        """)

        with gr.Tabs():
            # ── Tab 1: 真题词典 ──
            with gr.Tab("📖 真题词典"):
                chatbot = gr.Chatbot(height=400)
                msg = gr.Textbox(
                    placeholder="输入你的问题，例如：查一下 decline 在真题中的用法",
                    label="你的问题"
                )
                with gr.Row() as row1:
                    clear_btn = gr.Button("🗑️ 清空对话", size="sm")
                gr.Examples(
                    examples=[
                        "查一下 decline 在真题中的用法",
                        "environment 这个词在六级真题中怎么用的",
                        "帮我推荐一个六级备考计划",
                    ],
                    inputs=msg, label="💡 试试这些"
                )
                msg.submit(chat_fn, [msg, chatbot], [msg, chatbot])
                clear_btn.click(clear_fn, None, [chatbot, msg])

            # ── Tab 2: 作文批改 ──
            with gr.Tab("✍️ 作文批改"):
                gr.Markdown("### 把你的作文贴进来，一键批改")
                gr.Markdown("按四六级官方评分标准（满分15分），自动评分并给出建议。")
                with gr.Row():
                    with gr.Column(scale=7):
                        essay_input = gr.Textbox(label="你的作文", placeholder="把你的作文全文粘贴到这里...", lines=12)
                    with gr.Column(scale=3):
                        level_dropdown = gr.Dropdown(
                            choices=[("四级 CET-4", "cet4"), ("六级 CET-6", "cet6")],
                            value="cet6", label="考试级别", info="选择你备考的级别"
                        )
                with gr.Row():
                    essay_btn = gr.Button("📊 开始批改", variant="primary", size="lg")
                    clear_essay_btn = gr.Button("🗑️ 清空", size="lg")
                essay_output = gr.Markdown(label="批改结果", elem_classes="result-box markdown-output")
                gr.Examples(
                    examples=[
                        ["Nowadays, more and more people believe that environmental protection is crucial for our future. With the rapid development of industry, the pollution problem has become increasingly serious. We should take immediate action to protect our planet.", "cet6"],
                    ],
                    inputs=[essay_input, level_dropdown], label="📝 试一个例子"
                )
                # Enter 提交
                essay_input.submit(grade_essay, [essay_input, level_dropdown], essay_output)
                essay_btn.click(grade_essay, [essay_input, level_dropdown], essay_output)
                clear_essay_btn.click(lambda: ("", ""), None, [essay_input, essay_output])

            # ── Tab 3: 翻译批改 ──
            with gr.Tab("📝 翻译批改"):
                gr.Markdown("### 六级翻译评分标准")
                gr.Markdown("按 **信达雅** 三方面评分，满分 **15 分**。填入中文原文和你的英文译文，AI 自动评分。")
                with gr.Row():
                    with gr.Column():
                        original_input = gr.Textbox(label="中文原文", placeholder="粘贴中文原文句子或段落", lines=5)
                    with gr.Column():
                        translation_input = gr.Textbox(label="你的英文译文", placeholder="粘贴你的英文译文", lines=5)
                with gr.Row():
                    grade_btn = gr.Button("📊 开始评分", variant="primary", size="lg")
                    clear_grade_btn = gr.Button("🗑️ 清空", size="lg")
                grade_output = gr.Markdown(label="评分结果", elem_classes="result-box markdown-output")
                gr.Markdown("##### 试一个例子")
                with gr.Row():
                    example_btn1 = gr.Button("🌾 乡村振兴")
                    example_btn2 = gr.Button("📉 中档译文")
                    example_btn3 = gr.Button("🤖 人工智能")
                # Enter 提交
                original_input.submit(grade_translation, [original_input, translation_input], grade_output)
                translation_input.submit(grade_translation, [original_input, translation_input], grade_output)
                grade_btn.click(grade_translation, [original_input, translation_input], grade_output)
                clear_grade_btn.click(lambda: ("", "", ""), None, [original_input, translation_input, grade_output])
                example_btn1.click(lambda: grade_example("乡村振兴"), None, [original_input, translation_input])
                example_btn2.click(lambda: grade_example("中档译文"), None, [original_input, translation_input])
                example_btn3.click(lambda: grade_example("人工智能"), None, [original_input, translation_input])

            # ── Tab 4: 翻译原文与参考译文 ──
            from src.tools.translation_lookup import get_translation, list_available_exams as list_trans_exams
            trans_exam_choices = [(e, e) for e in list_trans_exams()]
            def lookup_translation_dd(exam):
                if not exam:
                    return "请选择考试"
                return get_translation(exam)
            with gr.Tab("📜 翻译原文"):
                gr.Markdown("### 查询六级翻译真题原文与参考译文")
                gr.Markdown("收录 **2016~2025 年共 52 套** 六级翻译真题的原文和参考译文。在下拉框中输入年份或关键词筛选。")
                with gr.Row():
                    trans_exam_dd = gr.Dropdown(
                        choices=trans_exam_choices,
                        label="选择考试",
                        info="输入年份快速筛选（如 2023）",
                        interactive=True
                    )
                trans_output = gr.Markdown(elem_classes="result-box markdown-output")
                trans_exam_dd.input(lookup_translation_dd, trans_exam_dd, trans_output)

            # ── Tab 5: 查答案 ──
            answer_exam_choices = [(e, e) for e in list_available_exams()]
            def lookup_answers_dd(exam, section):
                if not exam:
                    return "请选择考试"
                return format_exam_answers(exam, section)
            with gr.Tab("📋 查答案"):
                gr.Markdown("### 查询六级真题阅读答案")
                gr.Markdown("支持 **2023~2025 年 18 套六级** 阅读答案。选择考试后自动出结果。")
                with gr.Row():
                    answer_exam_dd = gr.Dropdown(
                        choices=answer_exam_choices,
                        label="选择考试",
                        info="输入年份快速筛选（如 2023）",
                        scale=7
                    )
                    answer_section_dd = gr.Dropdown(
                        choices=[("全部题型", "all"), ("Section A 选词填空", "cloze"), ("Section B 长篇阅读匹配", "sectionB"), ("Section C 仔细阅读", "reading")],
                        value="all", label="题型筛选", scale=3
                    )
                answer_output = gr.Markdown(elem_classes="result-box markdown-output")
                answer_exam_dd.input(lookup_answers_dd, [answer_exam_dd, answer_section_dd], answer_output)
                answer_section_dd.input(lookup_answers_dd, [answer_exam_dd, answer_section_dd], answer_output)

    return demo


def launch(share: bool = False, port: int = 0):
    demo = create_ui()
    actual_port = port or int(os.environ.get("PORT", 7860))
    demo.launch(share=share, server_port=actual_port, server_name="0.0.0.0", css=CUSTOM_CSS, theme=gr.themes.Soft())
