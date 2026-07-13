"""
Tests for the data_filtering module (T016).
"""
import ast
import json
import tempfile
from pathlib import Path
import pytest

from code.data_filtering import (
    parse_snippet_to_ast,
    extract_top_level_functions,
    filter_python_snippets,
    run_filtering_workflow
)
from code.data_model import CodeSnippet

def test_parse_snippet_valid():
    code = "def hello():\n    pass"
    tree = parse_snippet_to_ast(code)
    assert tree is not None
    assert isinstance(tree, ast.Module)

def test_parse_snippet_invalid():
    code = "def hello(\n    pass" # Missing closing paren
    tree = parse_snippet_to_ast(code)
    assert tree is None

def test_extract_top_level_functions_single():
    code = """
def foo():
    return 1

def bar():
    return 2
"""
    funcs = extract_top_level_functions(code)
    assert len(funcs) == 2
    assert "def foo()" in funcs[0]
    assert "def bar()" in funcs[1]

def test_extract_top_level_functions_nested():
    code = """
def outer():
    def inner():
  pass
    return inner
"""
    funcs = extract_top_level_functions(code)
    assert len(funcs) == 1
    assert "def outer()" in funcs[0]
    # inner should not be in the top-level list

def test_extract_top_level_functions_no_functions():
    code = "x = 1\ny = 2"
    funcs = extract_top_level_functions(code)
    assert len(funcs) == 0

def test_filter_python_snippets_language_filter():
    snippets = [
        {"id": "1", "language": "python", "code": "def f(): pass"},
        {"id": "2", "language": "javascript", "code": "function f() {}"},
        {"id": "3", "language": "Python", "code": "def g(): pass"}, # Case insensitive
        {"id": "4", "language": "java", "code": "void f() {}"}
    ]
    result = filter_python_snippets(snippets)
    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "3"
    assert all(s.language == "python" for s in result)

def test_filter_python_snippets_extraction():
    code = "def hello():\n    return 'world'"
    snippets = [
        {"id": "1", "language": "python", "code": code}
    ]
    result = filter_python_snippets(snippets)
    assert len(result) == 1
    assert "def hello()" in result[0].code
    assert result[0].length == len(code)

def test_filter_python_snippets_split_multiple_functions():
    code = """
def f1(): pass
def f2(): pass
"""
    snippets = [
        {"id": "1", "language": "python", "code": code}
    ]
    result = filter_python_snippets(snippets)
    # Should split into two snippets
    assert len(result) == 2
    assert result[0].id == "1_func_0"
    assert result[1].id == "1_func_1"
    assert "def f1()" in result[0].code
    assert "def f2()" in result[1].code

def test_filter_python_snippets_empty_functions():
    code = "x = 1"
    snippets = [
        {"id": "1", "language": "python", "code": code}
    ]
    result = filter_python_snippets(snippets)
    assert len(result) == 1
    assert result[0].code == code
    assert result[0].length == len(code)

def test_run_filtering_workflow(tmp_path):
    input_data = [
        {"id": "1", "language": "python", "code": "def a(): pass"},
        {"id": "2", "language": "java", "code": "void a() {}"},
        {"id": "3", "language": "python", "code": "def b(): return 1"}
    ]
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    
    with open(input_file, 'w') as f:
        json.dump(input_data, f)
    
    group = run_filtering_workflow(input_file, output_file, source_label="test")
    
    assert group.label == "test"
    assert len(group.snippets) == 2
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        saved_data = json.load(f)
    assert len(saved_data) == 2
    assert saved_data[0]["id"] == "1"
    assert saved_data[1]["id"] == "3"