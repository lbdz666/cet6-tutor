"""
Gradio Web 界面 — 四六级真题词典（优化版 v2）
"""
import gradio as gr
import os
import re
from src.agent.core import ReActAgent
from src.agent.tool_registry import ToolRegistry, Tool
from src.tools.word_lookup import word_lookup, WORD_LOOKUP_TOOL
from src.tools.exam_tools import check_essay, ESSAY_CHECK_TOOL
from src.tools.translation_eval import evaluate_translation, TRANSLATION_EVAL_TOOL
from src.tools.translation_eval_llm import evaluate_translation_llm, format_llm_report, TRANSLATION_EVAL_LLM_TOOL
from src.tools.exam_tools_llm import check_essay_llm, format_essay_llm_report, ESSAY_CHECK_LLM_TOOL
from src.tools.translation_lookup import get_translation, TRANSLATION_LOOKUP_TOOL
from src.tools.vocabulary import save_word, delete_word, list_words, get_words_list, SAVE_WORD_TOOL, DELETE_WORD_TOOL, LIST_WORDS_TOOL
from src.tools.essay_templates import format_template_preview, list_levels as tpl_list_levels, list_types as tpl_list_types, ESSAY_TEMPLATE_TOOL
from src.tools.answer_lookup import format_exam_answers, list_available_exams, ANSWER_LOOKUP_TOOL

# ── 全局 CSS ─────────────────────────────
CUSTOM_CSS = """
.gradio-container { max-width: 1200px !important; margin: 2rem auto !important; padding: 0 1.5rem !important; }
body { background: #1a1a2e !important; margin: 0 !important; }
h1 { font-size: 2rem !important; margin-bottom: 0.3rem !important; }
.tagline { color: #aaa !important; font-size: 1rem; margin-bottom: 1.5rem; }
/* 让所有输入框、下拉框、按钮占满宽度 */
.gr-box, .gr-form, input, select { width: 100% !important; }
/* 只调短翻译输入框的高度，作文输入框保持 */
textarea { width: 100% !important; }
/* 行内间距 */
.gr-row { gap: 0.8rem !important; }
/* 隐藏 Gradio 的冗余 footer */
footer { display: none !important; }
.result-box {
    border-left: 4px solid #4f86c6; padding: 0.8rem 1rem;
    background: #16213e !important; border-radius: 0 8px 8px 0;
    min-height: 80px;
}
.result-box, .result-box p, .result-box div, .result-box span,
.result-box *, .markdown-output, .markdown-output p, .markdown-output div {
    color: #e0e0e0 !important;
}
.result-box code, .markdown-output code {
    background: #0f3460 !important; color: #e0e0e0 !important; padding: 1px 5px !important; border-radius: 3px !important; font-size: 0.9em !important;
}
.result-box pre, .markdown-output pre {
    background: #0f3460 !important; color: #e0e0e0 !important; padding: 10px !important; border-radius: 5px !important; border: none !important;
}
button[role="tab"] { font-size: 0.95rem !important; padding: 8px 16px !important; }
button[role="tab"][aria-selected="true"] { border-bottom: 2px solid #4f86c6 !important; }
.star-btn { font-size: 1.6rem !important; padding: 2px 8px !important; min-width: 48px; background: transparent !important; border: none !important; cursor: pointer; transition: transform 0.2s; }
.star-btn:hover { transform: scale(1.3); }
"""


def build_agent() -> ReActAgent:
    registry = ToolRegistry()
    registry.register(Tool(name=WORD_LOOKUP_TOOL["name"], description=WORD_LOOKUP_TOOL["description"], fn=word_lookup, parameters=WORD_LOOKUP_TOOL["parameters"]))
    registry.register(Tool(name=ESSAY_CHECK_TOOL["name"], description=ESSAY_CHECK_TOOL["description"], fn=check_essay, parameters=ESSAY_CHECK_TOOL["parameters"]))
    registry.register(Tool(name=TRANSLATION_EVAL_TOOL["name"], description=TRANSLATION_EVAL_TOOL["description"], fn=evaluate_translation, parameters=TRANSLATION_EVAL_TOOL["parameters"]))
    registry.register(Tool(name=ANSWER_LOOKUP_TOOL["name"], description=ANSWER_LOOKUP_TOOL["description"], fn=format_exam_answers, parameters=ANSWER_LOOKUP_TOOL["parameters"]))
    registry.register(Tool(name=TRANSLATION_EVAL_LLM_TOOL["name"], description=TRANSLATION_EVAL_LLM_TOOL["description"], fn=evaluate_translation_llm, parameters=TRANSLATION_EVAL_LLM_TOOL["parameters"]))
    registry.register(Tool(name=ESSAY_CHECK_LLM_TOOL["name"], description=ESSAY_CHECK_LLM_TOOL["description"], fn=check_essay_llm, parameters=ESSAY_CHECK_LLM_TOOL["parameters"]))
    registry.register(Tool(name=TRANSLATION_LOOKUP_TOOL["name"], description=TRANSLATION_LOOKUP_TOOL["description"], fn=get_translation, parameters=TRANSLATION_LOOKUP_TOOL["parameters"]))
    registry.register(Tool(name=SAVE_WORD_TOOL["name"], description=SAVE_WORD_TOOL["description"], fn=save_word, parameters=SAVE_WORD_TOOL["parameters"]))
    registry.register(Tool(name=DELETE_WORD_TOOL["name"], description=DELETE_WORD_TOOL["description"], fn=delete_word, parameters=DELETE_WORD_TOOL["parameters"]))
    registry.register(Tool(name=LIST_WORDS_TOOL["name"], description=LIST_WORDS_TOOL["description"], fn=list_words, parameters=LIST_WORDS_TOOL["parameters"]))
    registry.register(Tool(name=ESSAY_TEMPLATE_TOOL["name"], description=ESSAY_TEMPLATE_TOOL["description"], fn=format_template_preview, parameters=ESSAY_TEMPLATE_TOOL["parameters"]))
    return ReActAgent(registry=registry)


def create_ui():
    agent = build_agent()

    # ── AI 问答 ─────────────────────────────
    def chat_fn(message, history):
        if not message or not message.strip():
            return "", history, ""
        try:
            response = agent.run(message)
        except Exception as e:
            response = f"⚠️ AI 服务暂不可用（{str(e)}）。你可以继续使用查答案、翻译原文等不需要AI的功能。"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        word = _extract_word(message)
        return "", history, word

    def clear_fn():
        agent.reset()
        return [], "", ""

    def _extract_word(text):
        """从用户输入中提取要查询的英文单词"""
        text = text.strip()
        # 模式: "查一下 X" / "查查 X" / "X 在真题" / "X 这个词"
        for pat in [r'查(?:一下|查)?\s+([a-zA-Z]+)', r'([a-zA-Z]+)\s+(?:在真题|这个词|的意思|的用法)']:
            m = re.search(pat, text)
            if m:
                return m.group(1).lower()
        # 如果输入就是一个单词
        words = re.findall(r'[a-zA-Z]{2,}', text)
        if len(words) == 1:
            return words[0].lower()
        return ""

    def star_state(word):
        """返回星标状态: (button_text, status_text)"""
        if not word:
            return "☆", ""
        words_list = get_words_list()
        saved = any(w["word"] == word.lower() for w in words_list)
        return ("⭐" if saved else "☆"), word

    def toggle_star(word, current_star):
        """点击星标: 收藏/取消收藏"""
        if not word:
            return "☆", "", ""
        w = word.lower().strip()
        if current_star == "⭐":
            msg = delete_word(w)
            return "☆", w, msg
        else:
            msg = save_word(w)
            return "⭐", w, msg

    # ── 生词本刷新函数（提前定义，供星标按钮调用）──
    def refresh_vocab():
        words = get_words_list()
        if not words:
            return "📭 生词本为空，查单词时点击 ⭐ 即可收藏"
        lines = ["## 📚 我的生词本", "", f"共 {len(words)} 个单词", "", "| # | 单词 | 中文释义 | 收藏时间 |", "|---|------|----------|----------|"]
        for i, w in enumerate(words, 1):
            defn = w.get('definition', '')[:50].replace('\n', ' ') if w.get('definition') else ''
            lines.append(f"| {i} | **{w['word']}** | {defn} | {w.get('saved_at', '?')} |")
        return "\n".join(lines)

    def vocab_add(word):
        if not word or not word.strip():
            return "请输入单词", refresh_vocab()
        return save_word(word.strip()), refresh_vocab()

    def vocab_delete(word):
        if not word or not word.strip():
            return "请输入单词", refresh_vocab()
        return delete_word(word.strip()), refresh_vocab()

    # ── 作文批改 ────────────────────────────
    def grade_essay(essay, level):
        if not essay or not essay.strip():
            return "请粘贴你的作文"
        rule_result = check_essay(essay.strip(), level)
        try:
            llm_result = check_essay_llm(essay.strip(), level)
            llm_report = format_essay_llm_report(llm_result)
            return rule_result + "\n\n" + llm_report
        except Exception as e:
            return rule_result + f"\n\n⚠️ AI 深度评分暂不可用（{str(e)}），以上为规则评分结果。"

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
        <div class="tagline">收录 2016~2025 年四六级真题 · 查单词 · 改作文 · 对答案 ⚡ v2.1</div>
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
                    star_btn = gr.Button("☆", size="sm", scale=1, elem_classes="star-btn")
                    word_label = gr.Markdown("", scale=2)
                    star_status = gr.Markdown("", visible=False)
                    clear_btn = gr.Button("🗑️ 清空对话", size="sm", scale=1)
                gr.Examples(
                    examples=[
                        "查一下 decline 在真题中的用法",
                        "environment 这个词在六级真题中怎么用的",
                        "帮我推荐一个六级备考计划",
                    ],
                    inputs=msg, label="💡 试试这些"
                )
                # 提交查询 → 聊天 + 更新星标
                event = msg.submit(chat_fn, [msg, chatbot], [msg, chatbot, word_label])
                event.then(star_state, word_label, [star_btn, word_label])
                # 点击星标 → 收藏/取消
                star_btn.click(toggle_star, [word_label, star_btn], [star_btn, word_label, star_status])
                clear_btn.click(clear_fn, None, [chatbot, msg, word_label])

            # ── Tab 2: 作文批改 + 模板（左右分栏）──
            tpl_levels = ["cet4", "cet6", "通用"]
            tpl_level_labels = {"cet4": "四级 CET-4", "cet6": "六级 CET-6", "通用": "通用"}
            def get_tpl_types(level):
                return tpl_list_types(level)
            def show_template(level, type_name):
                if not level or not type_name:
                    return "请选择级别和类型"
                return format_template_preview(level, type_name)
            with gr.Tab("✍️ 作文"):
                with gr.Row(equal_height=False):
                    with gr.Column(scale=7):
                        gr.Markdown("### ✍️ 批改")
                        essay_input = gr.Textbox(label="你的作文", placeholder="把你的作文全文粘贴到这里...", lines=10)
                        level_dropdown = gr.Dropdown(
                            choices=[("四级 CET-4", "cet4"), ("六级 CET-6", "cet6")],
                            value="cet6", label="考试级别"
                        )
                        with gr.Row():
                            essay_btn = gr.Button("📊 开始批改", variant="primary", size="lg")
                            clear_essay_btn = gr.Button("🗑️ 清空", size="lg")
                        essay_output = gr.Markdown(elem_classes="result-box markdown-output")
                        gr.Examples(
                            examples=[["Nowadays, more and more people believe that environmental protection is crucial for our future. With the rapid development of industry, the pollution problem has become increasingly serious. We should take immediate action to protect our planet.", "cet6"]],
                            inputs=[essay_input, level_dropdown], label="📝 试一个例子"
                        )
                        essay_input.submit(grade_essay, [essay_input, level_dropdown], essay_output)
                        essay_btn.click(grade_essay, [essay_input, level_dropdown], essay_output)
                        clear_essay_btn.click(lambda: ("", ""), None, [essay_input, essay_output])

                    with gr.Column(scale=5, elem_classes="right-panel"):
                        gr.Markdown("### 📝 模板")
                        tpl_level_dd = gr.Dropdown(
                            choices=[(tpl_level_labels[l], l) for l in tpl_levels],
                            value="cet6", label="级别"
                        )
                        tpl_type_dd = gr.Dropdown(
                            choices=[(t, t) for t in get_tpl_types("cet6")],
                            label="作文类型", value=get_tpl_types("cet6")[0] if get_tpl_types("cet6") else None
                        )
                        # 默认显示第一个模板
                        default_tpl = show_template("cet6", get_tpl_types("cet6")[0]) if get_tpl_types("cet6") else ""
                        tpl_output = gr.Markdown(default_tpl, elem_classes="result-box markdown-output")
                        tpl_level_dd.change(
                            fn=lambda l: gr.Dropdown(choices=[(t, t) for t in get_tpl_types(l)]),
                            inputs=tpl_level_dd, outputs=tpl_type_dd
                        )
                        tpl_level_dd.input(show_template, [tpl_level_dd, tpl_type_dd], tpl_output)
                        tpl_type_dd.input(show_template, [tpl_level_dd, tpl_type_dd], tpl_output)

            # ── Tab 3: 翻译批改 + 参考译文 ──
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
                original_input.submit(grade_translation, [original_input, translation_input], grade_output)
                translation_input.submit(grade_translation, [original_input, translation_input], grade_output)
                grade_btn.click(grade_translation, [original_input, translation_input], grade_output)
                clear_grade_btn.click(lambda: ("", "", ""), None, [original_input, translation_input, grade_output])
                example_btn1.click(lambda: grade_example("乡村振兴"), None, [original_input, translation_input])
                example_btn2.click(lambda: grade_example("中档译文"), None, [original_input, translation_input])
                example_btn3.click(lambda: grade_example("人工智能"), None, [original_input, translation_input])

                # ── 参考译文（原 Tab 4 合并进来）──
                gr.Markdown("---")
                gr.Markdown("### 📖 参考译文")
                gr.Markdown("批改完成后，选择对应考试查看官方参考译文：")
                from src.tools.translation_lookup import get_translation, list_available_exams as list_trans_exams
                trans_exam_choices = [(e, e) for e in list_trans_exams()]
                def lookup_translation_dd(exam):
                    if not exam:
                        return "请选择考试"
                    return get_translation(exam)
                with gr.Row():
                    trans_exam_dd = gr.Dropdown(
                        choices=trans_exam_choices,
                        label="选择考试",
                        info="输入年份快速筛选（如 2023）",
                        interactive=True
                    )
                trans_output = gr.Markdown(elem_classes="result-box markdown-output")
                trans_exam_dd.input(lookup_translation_dd, trans_exam_dd, trans_output)

            # ── Tab 4: 查答案 ──
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

            # ── Tab 5: 生词本 ──
            with gr.Tab("📚 生词本") as vocab_tab:
                gr.Markdown("### 收藏的单词")
                gr.Markdown("在「📖 真题词典」中查单词时，点击 ⭐ 收藏。也可以直接在这里添加/删除。")
                with gr.Row():
                    vocab_input = gr.Textbox(label="单词", placeholder="输入单词，如 economy", scale=4)
                    vocab_add_btn = gr.Button("➕ 收藏", variant="primary", scale=1)
                    vocab_del_btn = gr.Button("🗑️ 删除", scale=1)
                vocab_status = gr.Markdown("")
                vocab_list = gr.Markdown(refresh_vocab())
                # 切换到本标签页时自动刷新列表
                vocab_tab.select(refresh_vocab, None, vocab_list)
                vocab_add_btn.click(vocab_add, vocab_input, [vocab_status, vocab_list])
                vocab_del_btn.click(vocab_delete, vocab_input, [vocab_status, vocab_list])
                vocab_input.submit(vocab_add, vocab_input, [vocab_status, vocab_list])

    return demo


def launch(share: bool = False, port: int = 0):
    demo = create_ui()
    actual_port = port or int(os.environ.get("PORT", 7860))
    demo.launch(share=share, server_port=actual_port, server_name="0.0.0.0", css=CUSTOM_CSS, theme=gr.themes.Soft())
