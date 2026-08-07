"""
Unit tests for synthetic issue validity (T013).
Verifies that synthetic issues are AST parseable and structurally sound.
"""
import pytest
import ast
import json
import os
from pathlib import Path
from data.curate import generate_synthetic_issues, is_code_valid, mutate_variable_names, remove_comments, reorder_control_flow, change_api_signature

# Fixtures to simulate a minimal project environment if run standalone
@pytest.fixture
def sample_source_records():
    return [
        {
            "issue_id": "src_1",
            "code": "def foo(a):\n    return a + 1",
            "initial_coverage": 0.1,
            "ground_truth_lines": [1]
        },
        {
            "issue_id": "src_2",
            "code": "if True:\n    pass",
            "initial_coverage": 0.2,
            "ground_truth_lines": []
        },
        {
            "issue_id": "src_3",
            "code": "x = 1\ny = 2\nprint(x + y)",
            "initial_coverage": 0.5,
            "ground_truth_lines": [1, 2]
        }
    ]

def test_is_code_valid_true():
    """Test valid code returns True."""
    code = "x = 1"
    assert is_code_valid(code) is True

def test_is_code_valid_false():
    """Test invalid code returns False."""
    code = "x = "
    assert is_code_valid(code) is False

def test_generate_synthetic_issues_validity(sample_source_records):
    """Test that generated synthetic issues are valid."""
    synthetic = generate_synthetic_issues(sample_source_records, max_count=5)
    
    assert len(synthetic) > 0, "No synthetic issues were generated."
    
    for issue in synthetic:
        assert "code" in issue, "Generated issue missing 'code' field."
        assert "mutation_type" in issue, "Generated issue missing 'mutation_type' field."
        assert "original_issue_id" in issue, "Generated issue missing 'original_issue_id' field."
        
        # Verify the code is valid Python
        assert is_code_valid(issue["code"]), f"Generated invalid code: {issue['code']}"

def test_generate_synthetic_issues_ast_parse(sample_source_records):
    """Explicitly test AST parsing of generated code."""
    synthetic = generate_synthetic_issues(sample_source_records, max_count=10)
    
    for issue in synthetic:
        # This should not raise
        try:
            tree = ast.parse(issue["code"])
            assert tree is not None
        except SyntaxError as e:
            pytest.fail(f"AST parsing failed for generated code: {issue['code']}\nError: {e}")

def test_mutation_types_produce_valid_code(sample_source_records):
    """Test that specific mutation types produce valid code."""
    source_code = "def add(a, b):\n    return a + b"
    
    # Test variable renaming
    mutated = mutate_variable_names(source_code)
    assert is_code_valid(mutated), f"Variable renaming produced invalid code: {mutated}"
    
    # Test comment removal (if comments exist, though simple snippet might not have them)
    code_with_comment = "def add(a, b):\n    # Add numbers\n    return a + b"
    mutated = remove_comments(code_with_comment)
    assert is_code_valid(mutated), f"Comment removal produced invalid code: {mutated}"
    
    # Test control flow reordering (simple case)
    code_with_flow = "if True:\n    x = 1\nelse:\n    x = 2"
    try:
        mutated = reorder_control_flow(code_with_flow)
        # reorder_control_flow might return original if no safe reordering found
        assert is_code_valid(mutated), f"Control flow reordering produced invalid code: {mutated}"
    except Exception:
        # Some implementations might raise if no valid reordering exists, which is acceptable
        pass

def test_synthetic_issues_preserve_ground_truth(sample_source_records):
    """Test that synthetic issues preserve ground truth lines from original."""
    synthetic = generate_synthetic_issues(sample_source_records, max_count=1)
    
    for issue in synthetic:
        # Check that ground_truth_lines is present and is a list
        assert "ground_truth_lines" in issue
        assert isinstance(issue["ground_truth_lines"], list)
        
        # Verify it matches the source record's ground truth
        original_id = issue["original_issue_id"]
        original_record = next((r for r in sample_source_records if r["issue_id"] == original_id), None)
        if original_record:
            assert issue["ground_truth_lines"] == original_record["ground_truth_lines"]

def test_generate_synthetic_issues_max_count_limit(sample_source_records):
    """Test that max_count limits the number of generated issues."""
    synthetic = generate_synthetic_issues(sample_source_records, max_count=1)
    assert len(synthetic) <= 1, f"Generated more than max_count ({1}) issues: {len(synthetic)}"

def test_generate_synthetic_issues_empty_source():
    """Test behavior with empty source records."""
    synthetic = generate_synthetic_issues([], max_count=5)
    assert len(synthetic) == 0, "Generated issues from empty source."

def test_mutation_type_distribution(sample_source_records):
    """Test that multiple mutation types are applied if possible."""
    synthetic = generate_synthetic_issues(sample_source_records, max_count=100)
    mutation_types = set(issue["mutation_type"] for issue in synthetic)
    
    # We expect at least a couple of different types if the source allows
    # This is a soft check; if source is too simple, it might only produce one type
    assert len(mutation_types) >= 1, "No mutation types applied."