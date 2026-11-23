import json
import os
import tempfile
import pytest
from unittest.mock import patch

# We need to import the module. Since it's in code/, we might need to adjust path
# or assume the test runner sets up the path.
# For this unit test, we will mock the file system interactions and test the logic functions.

# Add code directory to path if running directly
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from append_sensitivity_comparison import (
    calculate_effect_size_difference,
    extract_metric_by_source,
    generate_sensitivity_summary,
    append_summary_to_json
)

def test_calculate_effect_size_difference():
    # Simple case
    a = [1.0, 2.0, 3.0]
    b = [4.0, 5.0, 6.0]
    # Mean a = 2, Mean b = 5. Diff = -3
    # Var a = 1, Var b = 1. Pooled Var = 1. Pooled Std = 1.
    # Cohen's d = -3 / 1 = -3.0
    result = calculate_effect_size_difference(a, b)
    assert result is not None
    assert abs(result - (-3.0)) < 0.001

def test_calculate_effect_size_zero_variance():
    a = [1.0, 1.0, 1.0]
    b = [2.0, 2.0, 2.0]
    result = calculate_effect_size_difference(a, b)
    assert result is None

def test_calculate_effect_size_empty():
    result = calculate_effect_size_difference([], [])
    assert result is None

def test_extract_metric_by_source():
    data = [
        {"task_id": "1", "source_type": "model_a", "metric_x": 10},
        {"task_id": "1", "source_type": "model_b", "metric_x": 20},
        {"task_id": "2", "source_type": "model_a", "metric_x": 15},
        {"task_id": "2", "source_type": "model_b", "metric_x": 25}
    ]
    
    vals_a = extract_metric_by_source(data, "metric_x", "model_a")
    assert vals_a == [10, 15]
    
    vals_b = extract_metric_by_source(data, "metric_x", "model_b")
    assert vals_b == [20, 25]

def test_generate_sensitivity_summary():
    # Mock data similar to what T045 would produce
    metrics_data = [
        {"task_id": "0", "source_type": "codegen-mono", "cyclomatic_complexity": 3.0, "halstead_volume": 18.0, "branch_coverage_pct": 95.0},
        {"task_id": "0", "source_type": "codellama-7b", "cyclomatic_complexity": 2.0, "halstead_volume": 16.0, "branch_coverage_pct": 100.0},
        {"task_id": "1", "source_type": "codegen-mono", "cyclomatic_complexity": 4.0, "halstead_volume": 25.0, "branch_coverage_pct": 80.0},
        {"task_id": "1", "source_type": "codellama-7b", "cyclomatic_complexity": 3.0, "halstead_volume": 23.0, "branch_coverage_pct": 100.0},
    ]
    
    summary = generate_sensitivity_summary(metrics_data)
    
    assert "metrics_analyzed" in summary
    assert "cyclomatic_complexity" in summary["metrics_analyzed"]
    assert "results" in summary
    
    cc_result = summary["results"]["cyclomatic_complexity"]
    assert cc_result["base_mean"] == 3.5
    assert cc_result["sensitivity_mean"] == 2.5
    assert "effect_size_cohen_d" in cc_result

def test_append_summary_to_json():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump([{"task_id": "1", "source_type": "A", "val": 1}], f)
        temp_path = f.name

    try:
        summary = {"test": "data", "value": 123}
        append_summary_to_json(temp_path, temp_path, summary)
        
        with open(temp_path, 'r') as f:
            result = json.load(f)
        
        assert "data" in result
        assert "metadata" in result
        assert result["metadata"]["sensitivity_comparison"]["test"] == "data"
    finally:
        os.unlink(temp_path)