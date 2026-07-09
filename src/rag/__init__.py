"""
RAG 检索器封装 — 四六级真题单词查询
内部使用 cet-rag-builder 的倒排索引
支持词干还原匹配 + 模糊搜索
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

# RAG 数据路径 — 优先项目本地 data/，其次 cet-rag-builder
_PROJECT_DATA = Path(__file__).parent.parent.parent / "data" / "inverted_index.json"
_RAG_BUILDER_DATA = Path.home() / "projects/cet-rag-builder/data/inverted_index.json"
RAG_INDEX_PATH = Path(os.environ.get(
    "CET_RAG_INDEX",
    str(_PROJECT_DATA if _PROJECT_DATA.exists() else _RAG_BUILDER_DATA)
))

def _stem(word: str) -> str:
    """使用 nltk PorterStemmer 进行词干还原，失败时返回原词"""
    try:
        from nltk.stem import PorterStemmer
        return PorterStemmer().stem(word)
    except Exception:
        return word

def _fuzzy_key(word: str) -> str:
    """
    清理单词用于索引匹配：
    - 转小写
    - 去标点（跟构建时的 tokenize 一致）
    """
    import string
    clean = word.translate(str.maketrans('', '', string.punctuation + '·–—…""''«»'))
    return clean.lower().strip()


class CETRag:
    """四六级真题 RAG 检索器"""

    def __init__(self, index_path: Optional[Path] = None):
        path = index_path or RAG_INDEX_PATH
        if not path.exists():
            # 尝试从 sentences.json 重建索引
            sent_path = path.parent / "sentences.json"
            if sent_path.exists():
                print("🔄 正在重建倒排索引...(首次部署需要约30秒)")
                self._build_index(sent_path, path)
            else:
                raise FileNotFoundError(
                    f"找不到索引文件: {path}\n"
                    f"请先运行 ~/projects/cet-rag-builder/build_rag.py 构建索引"
                )
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.index = data["index"]
        self.meta = data["meta"]
        self.word_count = len(self.index)

    def _build_index(self, sent_path: Path, out_path: Path):
        """从 sentences.json 重建倒排索引"""
        import string
        from collections import defaultdict

        with open(sent_path, "r", encoding="utf-8") as f:
            sentences = json.load(f)
        
        index = defaultdict(list)
        for i, s in enumerate(sentences):
            text = s.get("text", "") or s.get("sentence", "") or (s if isinstance(s, str) else "")
            if not text:
                continue
            exam = s.get("exam", f"sentence_{i}") if isinstance(s, dict) else f"sentence_{i}"
            year = s.get("year", "") if isinstance(s, dict) else ""
            
            words = text.lower().translate(str.maketrans('', '', string.punctuation + '·–—…""''«»')).split()
            seen = set()
            for w in words:
                if len(w) <= 1 or w in seen:
                    continue
                seen.add(w)
                # 词干还原
                try:
                    from nltk.stem import PorterStemmer
                    stem = PorterStemmer().stem(w)
                except Exception:
                    stem = w
                entry = {"sentence": text[:300], "exam": exam, "year": str(year)}
                if entry not in index.get(stem, []):
                    index[stem].append(entry)
        
        out_data = {"index": dict(index), "meta": {"source": "sentences.json", "count": len(index)}}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False)
        print(f"✅ 索引重建完成: {len(index)} 个词")

    def query(self, word: str, max_results: int = 20) -> list[dict]:
        """
        查询单词在真题中出现的位置（支持词干还原和模糊匹配）
        """
        raw_word = word.strip()
        # 清理标点（跟索引构建时的 tokenize 保持一致）
        word_clean = _fuzzy_key(raw_word)
        if not word_clean:
            return []

        results = []

        # 1. 精确匹配（最常见情况，最快）
        results = self.index.get(word_clean, [])
        if results:
            return self._sort_and_limit(results, max_results)

        # 2. 词干还原匹配 — study → studi 可匹配 studies/studying/studied
        stem = _stem(word_clean)
        if stem != word_clean:
            for indexed_word, entries in self.index.items():
                if _stem(indexed_word) == stem:
                    results.extend(entries)

        # 3. 部分匹配 — 搜索词是索引词的一部分
        if not results:
            for indexed_word, entries in self.index.items():
                if word_clean in indexed_word:
                    results.extend(entries)

        # 4. 前缀匹配 — 索引词以搜索词开头
        if not results:
            for indexed_word, entries in self.index.items():
                if indexed_word.startswith(word_clean):
                    results.extend(entries)

        # 5. 相近词匹配（编辑距离）
        if not results:
            try:
                from difflib import get_close_matches
                similar = get_close_matches(word_clean, self.index.keys(), n=5, cutoff=0.6)
                for s in similar:
                    results.extend(self.index.get(s, []))
            except Exception:
                pass

        return self._sort_and_limit(results, max_results)

    def _sort_and_limit(self, results: list[dict], limit: int) -> list[dict]:
        """按年份排序并截取"""
        results = sorted(results, key=lambda x: x.get("year", "0"), reverse=True)
        return results[:limit]

    def highlight(self, sentence: str, word: str) -> str:
        """在句子中标亮单词"""
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        return pattern.sub(lambda m: f"**{m.group()}**", sentence)

    def stats(self, word: str) -> dict:
        """单词统计"""
        from collections import Counter
        results = self.query(word, max_results=999)
        if not results:
            return {"total": 0, "by_exam": {}, "by_year": {}}
        
        by_exam = Counter(r["exam"] for r in results)
        by_year = Counter(r.get("year", "?") for r in results)
        return {
            "total": len(results),
            "by_exam": dict(by_exam.most_common()),
            "by_year": dict(by_year.most_common())
        }

    def format_result(self, results: list[dict], word: str) -> str:
        """格式化查询结果为可读文本"""
        if not results:
            return f"❌ 索引库中没有 \"{word}\""
        
        lines = [f"✅ \"{word}\" 出现在 {len(results)} 处:"]
        for i, r in enumerate(results[:15], 1):
            highlighted = self.highlight(r["sentence"][:200], word)
            lines.append(f"\n  [{i}] [{r['exam']}]")
            lines.append(f"     {highlighted}")
        if len(results) > 15:
            lines.append(f"\n  ... 还有 {len(results) - 15} 处")
        return "\n".join(lines)
