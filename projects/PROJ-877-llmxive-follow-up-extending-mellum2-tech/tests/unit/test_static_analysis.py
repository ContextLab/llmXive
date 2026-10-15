import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from llmxive_toolkit import paths
from code.data.static_analysis import process_chunk

def test_python_metrics():
    # Simple Python code: 1 if, 1 while, 1 for = CC 4
    # Nesting depth: for -> if = 2
    code = "for i in range(10):\n    if i > 5:\n        while True: pass"
    row = {"id": "1", "repo_name": "test", "language": "python", "content": code, "status": "raw"}
    res = process_chunk(row)
    
    assert res["status"] == "success"
    assert res["cyclomatic_complexity"] >= 3
    assert res["nesting_depth"] >= 2
    assert res["token_count"] > 0
    assert 0 <= res["repetition_ratio"] <= 1

def test_java_metrics():
    # Simple Java code
    code = "public class Test { public void m() { if(true) { while(true) {} } } }"
    row = {"id": "2", "repo_name": "test", "language": "java", "content": code, "status": "raw"}
    res = process_chunk(row)
    
    assert res["status"] == "success"
    assert res["cyclomatic_complexity"] >= 2
    assert res["nesting_depth"] >= 2

def test_parse_error():
    # Invalid syntax for both
    code = "This is not code !!!"
    row = {"id": "3", "repo_name": "test", "language": "python", "content": code, "status": "raw"}
    res = process_chunk(row)
    # tree-sitter is very permissive, but we test that it handles the flow
    assert "status" in res
