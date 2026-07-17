"""
Unit tests for synthetic issue validity (T011).
Verifies that synthetic issues are AST parseable.
"""
import pytest
import ast
from data.curate import generate_synthetic_issues, is_code_valid

def test_is_code_valid_true():
    """Test valid code returns True."""
    code = "x = 1"
    assert is_code_valid(code) is True

def test_is_code_valid_false():
    """Test invalid code returns False."""
    code = "x = "
    assert is_code_valid(code) is False

def test_generate_synthetic_issues_validity():
    """Test that generated synthetic issues are valid."""
    source_records = [
        {
            "issue_id": "src_1",
            "code": "def foo(a):\n    return a + 1",
            "initial_coverage": 0.1,
            "ground_truth_lines": [1]
        }
    ]
    
    synthetic = generate_synthetic_issues(source_records, max_count=5)
    
    for issue in synthetic:
        assert "code" in issue
        assert is_code_valid(issue["code"]) is True, f"Generated invalid code: {issue['code']}"
        assert "mutation_type" in issue

def test_generate_synthetic_issues_ast_parse():
    """Explicitly test AST parsing of generated code."""
    source_records = [
        {
            "issue_id": "src_2",
            "code": "if True:\n    pass",
            "initial_coverage": 0.2,
            "ground_truth_lines": []
        }
    ]
    
    synthetic = generate_synthetic_issues(source_records, max_count=1)
    
    for issue in synthetic:
        # This should not raise
        tree = ast.parse(issue["code"])
        assert tree is not None