import json
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_02_annotation_distillation.distill_rules import (
    load_schema,
    validate_rule_against_schema,
    check_ram_usage,
    load_annotated_failures,
    extract_rules_with_llm,
    calculate_coverage,
    run_distill_pipeline
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
            "task_id": "T001",
            "raw_error_log": "SyntaxError: invalid syntax",
            "ground_truth_resolution": "Fix indentation",
            "annotated_structural_feature": "Syntactic Error"
        },
        {
            "task_id": "T002",
            "raw_error_log": "NameError: name 'x' is not defined",
            "ground_truth_resolution": "Define variable x",
            "annotated_structural_feature": "Syntactic Error"
        },
        {
            "task_id": "T003",
            "raw_error_log": "While loop never terminates",
            "ground_truth_resolution": "Add break condition",
            "annotated_structural_feature": "Logical Loop"
        }
    ]

@pytest.fixture
def temp_files(sample_failures):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        failures_path = tmpdir_path / "failure_cases.json"
        with open(failures_path, "w") as f:
            json.dump(sample_failures, f)
        yield {"failures_path": failures_path}

def test_validate_rule_against_schema_valid(sample_schema):
    rule = {
        "rule_id": "R001",
        "condition_pattern": "SyntaxError",
        "pivot_action": "Fix",
        "confidence": 0.9
    }
    assert validate_rule_against_schema(rule, sample_schema) is True

def test_validate_rule_against_schema_invalid(sample_schema):
    rule = {
        "rule_id": "R001",
        "condition_pattern": "SyntaxError"
        # Missing pivot_action and confidence
    }
    assert validate_rule_against_schema(rule, sample_schema) is False

def test_load_annotated_failures(temp_files):
    failures = load_annotated_failures(temp_files["failures_path"])
    assert len(failures) == 3
    assert failures[0]["task_id"] == "T001"

def test_extract_rules_with_llm(sample_failures):
    rules = extract_rules_with_llm(sample_failures, n_gram=3, quantization="int8")
    assert len(rules) > 0
    assert rules[0]["rule_id"].startswith("RULE-")
    assert "condition_pattern" in rules[0]
    assert "pivot_action" in rules[0]

def test_calculate_coverage(sample_failures):
    # Create a rule that matches all
    rules = [
        {
            "rule_id": "R001",
            "condition_pattern": ".*",
            "pivot_action": "Fix",
            "confidence": 1.0
        }
    ]
    coverage = calculate_coverage(rules, sample_failures)
    assert coverage == 1.0

    # Create a rule that matches none
    rules_none = [
        {
            "rule_id": "R002",
            "condition_pattern": "zzz_nonexistent_error",
            "pivot_action": "Fix",
            "confidence": 1.0
        }
    ]
    coverage_none = calculate_coverage(rules_none, sample_failures)
    assert coverage_none == 0.0

def test_check_ram_usage_under_limit():
    with patch('psutil.Process') as mock_process:
        mock_memory = MagicMock()
        mock_memory.rss = 2 * (1024 ** 3) # 2GB
        mock_process.return_value.memory_info.return_value = mock_memory
        ram = check_ram_usage()
        assert ram == 2.0

def test_check_ram_usage_over_limit():
    with patch('psutil.Process') as mock_process:
        mock_memory = MagicMock()
        mock_memory.rss = 8 * (1024 ** 3) # 8GB
        mock_process.return_value.memory_info.return_value = mock_memory
        with pytest.raises(MemoryError):
            check_ram_usage()

def test_check_ram_usage_fallback_triggered():
    with patch('os.environ.get', return_value="1"):
        with pytest.raises(RuntimeError):
            check_ram_usage()

def test_run_distill_pipeline(sample_failures):
    # Split manually for test
    train = sample_failures[:2]
    val = sample_failures[2:]
    
    rules, coverage = run_distill_pipeline(train, val, attempt=1)
    assert isinstance(rules, list)
    assert isinstance(coverage, float)
    assert coverage >= 0.0 and coverage <= 1.0
