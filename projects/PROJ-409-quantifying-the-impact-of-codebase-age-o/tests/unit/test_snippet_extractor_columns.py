"""Tests that snippet_extractor.py always emits token_length and complexity."""

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from extraction.snippet_extractor import (  # noqa: E402
    ComplexityCalculator,
    TokenCounter,
    extract_functions,
    extract_snippets_from_directory,
    extract_snippets_from_file,
)

SAMPLE = '''\
def simple_function(a, b):
    """Add two numbers."""
    total = a + b
    if total > 10:
        total = total - 1
    for i in range(3):
        total += i
    return total


def another_function(values):
    result = []
    for v in values:
        if v % 2 == 0:
            result.append(v * 2)
        else:
            result.append(v)
    return result
'''


def _write_sample(tmp_path: Path) -> Path:
    f = tmp_path / "sample.py"
    f.write_text(SAMPLE, encoding="utf-8")
    return f


def test_token_counter_counts_tokens():
    count = TokenCounter.count("def f():\n    return 1\n")
    assert count > 0
    assert TokenCounter.length("def f():\n    return 1\n") == count


def test_complexity_calculator_positive():
    calc = ComplexityCalculator()
    tree = ast.parse(SAMPLE)
    funcs = extract_functions(tree)
    assert len(funcs) == 2
    for func in funcs:
        assert calc.calculate(func) >= 1


def test_file_extraction_has_required_columns(tmp_path):
    f = _write_sample(tmp_path)
    snippets = extract_snippets_from_file(f, min_tokens=10)
    assert len(snippets) >= 1
    for s in snippets:
        assert "token_length" in s, "missing token_length column"
        assert "complexity" in s, "missing complexity column"
        assert s["token_length"] is not None
        assert s["complexity"] is not None
        assert isinstance(s["token_length"], int)
        assert isinstance(s["complexity"], int)
        assert s["token_length"] >= 10
        assert s["complexity"] >= 1
        assert s["token_count"] == s["token_length"]


def test_directory_extraction_has_required_columns(tmp_path):
    _write_sample(tmp_path)
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "other.py").write_text(SAMPLE, encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not python", encoding="utf-8")
    snippets = extract_snippets_from_directory(tmp_path, min_tokens=10)
    assert len(snippets) >= 2
    for s in snippets:
        assert "token_length" in s
        assert "complexity" in s
        assert "file_path" in s
        assert s["token_length"] >= 10
        assert s["complexity"] >= 1


def test_min_token_filter(tmp_path):
    f = _write_sample(tmp_path)
    snippets = extract_snippets_from_file(f, min_tokens=10000)
    assert snippets == []


def test_non_python_file_ignored(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text(SAMPLE, encoding="utf-8")
    assert extract_snippets_from_file(f) == []