---
title: 四六级真题词典
emoji: 📖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.19.0
app_file: app.py
pinned: false
---

# 📖 四六级真题词典

收录 2016~2025 年四六级真题，支持查单词、作文批改、学习答疑。

## 🚀 功能

- 🔍 **查单词** — 输入单词，在十年真题中查找它的用法和例句
- ✍️ **作文检查** — 检查作文字数和基本结构
- 💡 **学习建议** — 语法、阅读、翻译等问题答疑

## 🔑 配置

在 Space 的 **Settings → Secrets** 中添加以下密钥：

| 密钥 | 说明 | 示例值 |
|------|------|--------|
| `LLM_API_KEY` | API 密钥 | `sk-xxxxx` |
| `LLM_BASE_URL` | API 地址（可选） | `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名（可选） | `deepseek-chat` |

默认使用 DeepSeek API，如需更换通义千问等：
```
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

## 🗂️ 项目结构

```
├── app.py              # Spaces 入口
├── main.py             # 本地入口
├── src/
│   ├── agent/          # ReAct 循环 + LLM + 记忆
│   ├── rag/            # 真题检索
│   ├── tools/          # 工具函数
│   └── ui/             # Gradio 界面
└── data/               # RAG 索引数据
```
