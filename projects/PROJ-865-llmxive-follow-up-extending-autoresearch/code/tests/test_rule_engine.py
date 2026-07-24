import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_03_execution.rule_engine import (
    load_rules_library,
    load_annotated_failures,
    parse_error_log,
    match_rule,
    get_baseline_retrieval_method,
    execute_pivot_action,
    run_rule_engine_on_failures,
    save_results
)

@pytest.fixture
def sample_rules():
    return [
        {
            "rule_id": "RULE_001",
            "condition_pattern": "Syntactic Error",
            "pivot_action": "fix_syntax",
            "confidence": 0.95
        },
        {
            "rule_id": "RULE_002",
            "condition_pattern": "Logical Loop",
            "pivot_action": "break_loop",
            "confidence": 0.90
        },
        {
            "rule_id": "RULE_003",
            "condition_pattern": "Unstructured",
            "pivot_action": "fallback_retrieval",
            "confidence": 0.80
        }
    ]

@pytest.fixture
def sample_failures():
    return [
        {
            "task_id": "TASK_001",
            "raw_error_log": "SyntaxError: invalid syntax",
            "ground_truth_resolution": "fixed_syntax",
            "annotated_structural_feature": "Syntactic Error"
        },
        {
            "task_id": "TASK_002",
            "raw_error_log": "Infinite loop detected in function",
            "ground_truth_resolution": "break_loop",
            "annotated_structural_feature": "Logical Loop"
        },
        {
            "task_id": "TASK_003",
            "raw_error_log": "Some random error message",
            "ground_truth_resolution": "unknown",
            "annotated_structural_feature": "Unstructured"
        }
    ]

def test_parse_error_log_syntax_error():
    """Test parsing of syntax error logs."""
    error_log = "SyntaxError: invalid syntax at line 10"
    parsed = parse_error_log(error_log)
    
    assert parsed["syntax_error"] is True
    assert parsed["logical_loop"] is False
    assert parsed["unstructured"] is False
    assert "syntax" in parsed["keywords"]

def test_parse_error_log_logical_loop():
    """Test parsing of logical loop error logs."""
    error_log = "Infinite loop detected in the recursive function"
    parsed = parse_error_log(error_log)
    
    assert parsed["logical_loop"] is True
    assert parsed["syntax_error"] is False
    assert "loop" in parsed["keywords"]

def test_parse_error_log_unstructured():
    """Test parsing of unstructured error logs."""
    error_log = "Some random error that doesn't match any pattern"
    parsed = parse_error_log(error_log)
    
    assert parsed["unstructured"] is True
    assert parsed["syntax_error"] is False
    assert parsed["logical_loop"] is False

def test_parse_error_log_empty():
    """Test parsing of empty error logs."""
    parsed = parse_error_log("")
    
    assert parsed["unstructured"] is True

def test_match_rule_syntax_error(sample_rules):
    """Test rule matching for syntactic errors."""
    parsed_error = {
        "raw": "SyntaxError: invalid syntax",
        "syntax_error": True,
        "logical_loop": False,
        "semantic_ambiguity": False,
        "missing_context": False,
        "unstructured": False,
        "keywords": ["syntax"]
    }
    
    matched_rule = match_rule(parsed_error, sample_rules)
    
    assert matched_rule is not None
    assert matched_rule["rule_id"] == "RULE_001"
    assert matched_rule["condition_pattern"] == "Syntactic Error"

def test_match_rule_logical_loop(sample_rules):
    """Test rule matching for logical loops."""
    parsed_error = {
        "raw": "Infinite loop detected",
        "syntax_error": False,
        "logical_loop": True,
        "semantic_ambiguity": False,
        "missing_context": False,
        "unstructured": False,
        "keywords": ["loop"]
    }
    
    matched_rule = match_rule(parsed_error, sample_rules)
    
    assert matched_rule is not None
    assert matched_rule["rule_id"] == "RULE_002"

def test_match_rule_no_match(sample_rules):
    """Test rule matching when no rule matches."""
    parsed_error = {
        "raw": "Unknown error",
        "syntax_error": False,
        "logical_loop": False,
        "semantic_ambiguity": False,
        "missing_context": False,
        "unstructured": True,
        "keywords": []
    }
    
    matched_rule = match_rule(parsed_error, sample_rules)
    
    # Should match the Unstructured rule
    assert matched_rule is not None
    assert matched_rule["rule_id"] == "RULE_003"

def test_get_baseline_retrieval_method():
    """Test baseline retrieval method."""
    method = get_baseline_retrieval_method()
    
    assert method == "baseline_retrieval_fallback"

def test_execute_pivot_action_with_rule(sample_rules):
    """Test executing pivot action with a matched rule."""
    parsed_error = {
        "raw": "SyntaxError: invalid syntax",
        "syntax_error": True,
        "logical_loop": False,
        "semantic_ambiguity": False,
        "missing_context": False,
        "unstructured": False,
        "keywords": ["syntax"]
    }
    
    matched_rule = match_rule(parsed_error, sample_rules)
    success, time_to_pivot, action = execute_pivot_action(matched_rule, parsed_error)
    
    assert success is True
    assert time_to_pivot > 0
    assert action == "fix_syntax"

def test_execute_pivot_action_no_rule(sample_rules):
    """Test executing pivot action when no rule matches."""
    parsed_error = {
        "raw": "Unknown error",
        "syntax_error": False,
        "logical_loop": False,
        "semantic_ambiguity": False,
        "missing_context": False,
        "unstructured": True,
        "keywords": []
    }
    
    matched_rule = None
    success, time_to_pivot, action = execute_pivot_action(matched_rule, parsed_error)
    
    assert success is False
    assert time_to_pivot > 0
    assert action == "baseline_retrieval_fallback"

def test_run_rule_engine_on_failures(sample_rules, sample_failures, tmp_path):
    """Test running the rule engine on failure cases."""
    output_path = tmp_path / "test_results.csv"
    
    results = run_rule_engine_on_failures(sample_failures, sample_rules, output_path)
    
    assert len(results) == 3
    
    # Check first result (syntax error)
    assert results[0]["task_id"] == "TASK_001"
    assert results[0]["success"] is True
    assert results[0]["matched_rule_id"] == "RULE_001"
    
    # Check second result (logical loop)
    assert results[1]["task_id"] == "TASK_002"
    assert results[1]["success"] is True
    assert results[1]["matched_rule_id"] == "RULE_002"
    
    # Check third result (unstructured)
    assert results[2]["task_id"] == "TASK_003"
    assert results[2]["success"] is False
    assert results[2]["matched_rule_id"] is None

def test_save_results(sample_rules, sample_failures, tmp_path):
    """Test saving results to CSV."""
    output_path = tmp_path / "test_results.csv"
    
    results = run_rule_engine_on_failures(sample_failures, sample_rules, output_path)
    
    assert output_path.exists()
    
    # Read and verify CSV content
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 4  # Header + 3 results
    assert "task_id" in lines[0]
    assert "method" in lines[0]
    assert "time_to_pivot" in lines[0]
    assert "success" in lines[0]
    assert "failure_type" in lines[0]
