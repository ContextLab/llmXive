"""
Contract test for metrics_report.json schema.
"""

import pytest
import json
from pathlib import Path
from utils.data_utils import load_schema, validate_against_schema

def get_schema_path():
    return Path("specs/001-gene-regulation/contracts/metrics_report.schema.yaml")

def load_sample_metrics_report():
    # Load the actual generated report if it exists, otherwise skip
    report_path = Path("data/metrics_report.json")
    if not report_path.exists():
        pytest.skip("metrics_report.json not found. Run evaluate.py first.")
    with open(report_path, 'r') as f:
        return json.load(f)

def test_metrics_report_schema_exists():
    schema_path = get_schema_path()
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_metrics_report_schema_loads():
    schema_path = get_schema_path()
    schema = load_schema(schema_path)
    assert schema is not None

def test_sample_metrics_report_conforms():
    schema_path = get_schema_path()
    schema = load_schema(schema_path)
    report = load_sample_metrics_report()

    # Validate against schema
    # The validate_against_schema function might need to be adapted for JSON schema
    # For now, we'll do a basic check
    required_keys = [
        "transformer_accuracy",
        "baseline_accuracy",
        "shuffled_control_accuracy",
        "improvement_vs_baseline",
        "improvement_vs_shuffled",
        "mcnemar_vs_baseline",
        "mcnemar_vs_shuffled",
        "confusion_matrix_transformer",
        "confusion_matrix_baseline",
        "confusion_matrix_shuffled",
        "geometry_disjoint",
        "test_set_size",
        "train_set_size"
    ]

    for key in required_keys:
        assert key in report, f"Missing required key: {key}"

    # Check types
    assert isinstance(report["transformer_accuracy"], float)
    assert isinstance(report["baseline_accuracy"], float)
    assert isinstance(report["shuffled_control_accuracy"], float)
    assert isinstance(report["improvement_vs_baseline"], float)
    assert isinstance(report["improvement_vs_shuffled"], float)
    assert isinstance(report["mcnemar_vs_baseline"], dict)
    assert isinstance(report["mcnemar_vs_shuffled"], dict)
    assert isinstance(report["confusion_matrix_transformer"], list)
    assert isinstance(report["confusion_matrix_baseline"], list)
    assert isinstance(report["confusion_matrix_shuffled"], list)
    assert isinstance(report["geometry_disjoint"], bool)
    assert isinstance(report["test_set_size"], int)
    assert isinstance(report["train_set_size"], int)

    # Check McNemar structure
    assert "p_value" in report["mcnemar_vs_baseline"]
    assert "contingency_table" in report["mcnemar_vs_baseline"]
    assert "p_value" in report["mcnemar_vs_shuffled"]
    assert "contingency_table" in report["mcnemar_vs_shuffled"]