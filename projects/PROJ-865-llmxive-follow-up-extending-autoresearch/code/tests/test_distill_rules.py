import json
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code_02_annotation_distillation.distill_rules import (
    load_schema,
    validate_rule_against_schema,
    check_ram_usage,
    load_annotated_failures,
    extract_rules_with_llm,
    calculate_coverage,
    run_distill_pipeline,
    main
)

@pytest.fixture
def sample_schema():
    return {
        "type": "object",
        "properties": {
            "rule_id": {"type": "string"},
            "condition_pattern": {"type": "string"},
            "pivot_action": {"type": "string"},
            "confidence": {"type": "number"}
        },
        "required": ["rule_id", "condition_pattern", "pivot_action", "confidence"]
    }

@pytest.fixture
def sample_failures():
    return [
        {
            "task_id": "task-001",
            "raw_error_log": "SyntaxError: invalid syntax at line 10",
            "ground_truth_resolution": "Fix syntax error",
            "annotated_structural_feature": "Syntactic Error"
        },
        {
            "task_id": "task-002",
            "raw_error_log": "Infinite loop detected in function calculate()",
            "ground_truth_resolution": "Break loop",
            "annotated_structural_feature": "Logical Loop"
        },
        {
            "task_id": "task-003",
            "raw_error_log": "Ambiguous variable name 'x' used in multiple contexts",
            "ground_truth_resolution": "Clarify context",
            "annotated_structural_feature": "Semantic Ambiguity"
        }
    ]

@pytest.fixture
def temp_files(sample_failures):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create sample failure file
        failure_file = tmpdir / "failures.json"
        with open(failure_file, 'w') as f:
            json.dump(sample_failures, f)
        
        # Create validation split
        val_file = tmpdir / "val_failures.json"
        with open(val_file, 'w') as f:
            json.dump(sample_failures[:2], f)
        
        yield tmpdir, failure_file, val_file

def test_validate_rule_against_schema_valid(sample_schema):
    valid_rule = {
        "rule_id": "RULE-001",
        "condition_pattern": r"\bsyntax\b",
        "pivot_action": "Fix syntax",
        "confidence": 0.95
    }
    assert validate_rule_against_schema(valid_rule, sample_schema) is True

def test_validate_rule_against_schema_invalid(sample_schema):
    invalid_rule = {
        "rule_id": "RULE-001",
        "condition_pattern": r"\bsyntax\b",
        "pivot_action": "Fix syntax"
        # Missing confidence
    }
    assert validate_rule_against_schema(invalid_rule, sample_schema) is False

def test_load_annotated_failures(temp_files):
    _, failure_file, _ = temp_files
    failures = load_annotated_failures(failure_file)
    assert len(failures) == 3
    assert failures[0]["task_id"] == "task-001"

def test_extract_rules_with_llm(sample_failures):
    rules = extract_rules_with_llm(sample_failures, ngram=3, quantization="int8")
    assert len(rules) > 0
    # Check that rules have required fields
    for rule in rules:
        assert "rule_id" in rule
        assert "condition_pattern" in rule
        assert "pivot_action" in rule
        assert "confidence" in rule

def test_calculate_coverage(sample_failures):
    # Create a rule that matches the first failure
    rules = [
        {
            "rule_id": "TEST-RULE",
            "condition_pattern": r"\bsyntax\b",
            "pivot_action": "Fix syntax",
            "confidence": 0.9
        }
    ]
    coverage = calculate_coverage(rules, sample_failures)
    # Only the first failure matches
    assert coverage == pytest.approx(1/3, abs=0.01)

def test_run_distill_pipeline(temp_files):
    _, all_file, val_file = temp_files
    all_failures = load_annotated_failures(all_file)
    val_failures = load_annotated_failures(val_file)
    
    rules, coverage, attempt = run_distill_pipeline(val_failures, all_failures)
    
    assert len(rules) > 0
    assert 0.0 <= coverage <= 1.0
    assert attempt >= 0

@patch('code_02_annotation_distillation.distill_rules.psutil.Process')
def test_check_ram_usage_under_limit(mock_process, temp_files):
    mock_mem = MagicMock()
    mock_mem.rss = 5 * 1024 ** 3  # 5 GB
    mock_process.return_value.memory_info.return_value = mock_mem
    
    # Should return False (under limit)
    assert check_ram_usage() is False

@patch('code_02_annotation_distillation.distill_rules.psutil.Process')
def test_check_ram_usage_over_limit(mock_process, temp_files):
    mock_mem = MagicMock()
    mock_mem.rss = 8 * 1024 ** 3  # 8 GB
    mock_process.return_value.memory_info.return_value = mock_mem
    
    # Should return True (over limit)
    assert check_ram_usage() is True

def test_main_execution(temp_files, sample_schema, caplog):
    # Mock schema loading to avoid file dependency
    with patch('code_02_annotation_distillation.distill_rules.load_schema', return_value=sample_schema):
        with patch('code_02_annotation_distillation.distill_rules.SCHEMA_PATH', Path("/fake/schema.yaml")):
            with patch('code_02_annotation_distillation.distill_rules.FAILURE_CASES_PATH', temp_files[1]):
                with patch('code_02_annotation_distillation.distill_rules.VAL_SPLIT_PATH', temp_files[2]):
                    with patch('code_02_annotation_distillation.distill_rules.RULES_LIBRARY_PATH', temp_files[0] / "rules.json"):
                        with patch('code_02_annotation_distillation.distill_rules.COVERAGE_REPORT_PATH', temp_files[0] / "coverage.json"):
                            with patch('code_02_annotation_distillation.distill_rules.FALLBACK_STATUS_PATH', temp_files[0] / "fallback.json"):
                                with patch.dict(os.environ, {"FALLBACK_TRIGGERED": "0"}):
                                    main()
                                    
                                    # Verify output files were created
                                    assert (temp_files[0] / "rules.json").exists()
                                    assert (temp_files[0] / "coverage.json").exists()
                                    
                                    # Verify content
                                    with open(temp_files[0] / "rules.json") as f:
                                        rules = json.load(f)
                                        assert len(rules) > 0
                                    
                                    with open(temp_files[0] / "coverage.json") as f:
                                        coverage_data = json.load(f)
                                        assert "coverage_percentage" in coverage_data
                                        assert "threshold" in coverage_data