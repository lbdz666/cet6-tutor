"""Hugging Face Spaces 入口 — 四六级真题词典"""
import sys, os

# 项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.app import create_ui, launch

# HF Spaces 会直接导入并运行 demo
demo = create_ui()

if __name__ == "__main__":
    # Spaces 上 server_name="0.0.0.0" 自动生效
    launch()
