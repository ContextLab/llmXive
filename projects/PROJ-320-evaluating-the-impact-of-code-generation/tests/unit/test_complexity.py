"""
Unit tests for the complexity analysis helpers (T008).

These tests verify that the fallback metric (added + removed lines) is
non‑negative and that a trivially simple diff yields a cyclomatic
complexity of 1 when the full AST analysis is used.
"""
import pytest

from code.analysis.complexity import (
    calculate_loc,
    calculate_cyclomatic_complexity_ast,
    extract_added_removed_lines,
    analyze_diff_complexity,
)

def test_calculate_loc_counts_nonempty_lines():
    code = "def foo():\n    pass\n\n# comment line\n"
    assert calculate_loc(code) == 2  # two real code lines

def test_cyclomatic_complexity_simple_function():
    code = "def foo():\n    return 1"
    assert calculate_cyclomatic_complexity_ast(code) == 1

def test_cyclomatic_complexity_with_if():
    code = "def foo(x):\n    if x > 0:\n        return x\n    else:\n        return -x"
    # base 1 + one if => 2
    assert calculate_cyclomatic_complexity_ast(code) == 2

def test_extract_added_removed_lines_counts_correctly():
    diff = (
        "diff --git a/file.py b/file.py\n"
        "index 123..456 100644\n"
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,3 +1,4 @@\n"
        "-old line\n"
        "+new line 1\n"
        "+new line 2\n"
    )
    added, removed = extract_added_removed_lines(diff)
    assert added == 2
    assert removed == 1

def test_analyze_diff_complexity_simple_addition():
    diff = (
        "diff --git a/file.py b/file.py\n"
        "+++ b/file.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def hello():\n"
        "+    print('hi')\n"
    )
    metrics = analyze_diff_complexity(diff)
    # Two lines of code, no decision points => cyclomatic = 1
    assert metrics["loc"] == 2
    assert metrics["cyclomatic"] == 1