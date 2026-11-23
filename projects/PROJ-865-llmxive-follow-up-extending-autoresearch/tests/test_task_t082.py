"""
Tests for T082: Pilot Distillation on Small Subset
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from annotation.distill_rules import (
    validate_rule_against_schema,
    extract_rules_regex,
    calculate_coverage,
    run_distill_pipeline
)

@pytest.fixture
def sample_failures():
    return [
        {
            "task_id": "task_001",
            "raw_error_log": "SyntaxError: invalid syntax on line 10",
            "annotated_structural_feature": "Syntactic Error"
        },
        {
            "task_id": "task_002",
            "raw_error_log": "RecursionError: maximum recursion depth exceeded",
            "annotated_structural_feature": "Logical Loop"
        },
        {
            "task_id": "task_003",
            "raw_error_log": "The meaning is ambiguous and unclear",
            "annotated_structural_feature": "Semantic Ambiguity"
        },
        {
            "task_id": "task_004",
            "raw_error_log": "Variable 'x' is missing context",
            "annotated_structural_feature": "Missing Context"
        },
        {
            "task_id": "task_005",
            "raw_error_log": "Some random unstructured error message",
            "annotated_structural_feature": "Unstructured"
        }
    ]

def test_validate_rule_valid():
    rule = {
        "rule_id": "RULE_0001",
        "condition_pattern": r"SyntaxError.*",
        "pivot_action": "Refactor syntax",
        "confidence": 0.95
    }
    valid, reason = validate_rule_against_schema(rule, {})
    assert valid is True
    assert reason is None

def test_validate_rule_missing_key():
    rule = {
        "rule_id": "RULE_0001",
        "condition_pattern": r"SyntaxError.*",
        "pivot_action": "Refactor syntax"
    }
    valid, reason = validate_rule_against_schema(rule, {"required": ["confidence"]})
    assert valid is False
    assert "Missing required key: confidence" in reason

def test_validate_rule_invalid_confidence():
    rule = {
        "rule_id": "RULE_0001",
        "condition_pattern": r"SyntaxError.*",
        "pivot_action": "Refactor syntax",
        "confidence": 1.5
    }
    valid, reason = validate_rule_against_schema(rule, {})
    assert valid is False
    assert "confidence must be between 0 and 1" in reason

def test_extract_rules_regex(sample_failures):
    rules = extract_rules_regex(sample_failures)
    assert len(rules) > 0
    # Check that we have at least a few rules
    assert any("SyntaxError" in r["condition_pattern"] for r in rules)
    assert any("recursion" in r["condition_pattern"].lower() for r in rules)
    assert any("ambiguous" in r["condition_pattern"].lower() for r in rules)

def test_calculate_coverage(sample_failures):
    rules = extract_rules_regex(sample_failures)
    coverage = calculate_coverage(rules, sample_failures)
    assert "coverage_percentage" in coverage
    assert "total_cases" in coverage
    assert coverage["total_cases"] == len(sample_failures)
    assert coverage["coverage_percentage"] >= 0
    assert coverage["coverage_percentage"] <= 100

def test_run_distill_pipeline_integration(sample_failures):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_path = tmpdir / "failures.json"
        rules_path = tmpdir / "rules.json"
        coverage_path = tmpdir / "coverage.json"

        # Write sample failures
        with open(input_path, 'w') as f:
            json.dump(sample_failures, f)

        # Run pipeline
        result = run_distill_pipeline(
            input_path=input_path,
            output_rules_path=rules_path,
            output_coverage_path=coverage_path,
            subset_size=3,
            validate_schema=True
        )

        # Verify outputs
        assert rules_path.exists()
        assert coverage_path.exists()

        with open(rules_path, 'r') as f:
            rules = json.load(f)
        assert len(rules) > 0

        with open(coverage_path, 'r') as f:
            coverage = json.load(f)
        assert "coverage_percentage" in coverage
        # With subset_size=3, we should have coverage calculated on 3 items
        assert coverage["total_cases"] == 3
