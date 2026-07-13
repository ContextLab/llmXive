"""
Integration test for Task T040: Create comparison report.
Verifies that the comparison report is generated correctly with valid diffs.
"""
import os
import json
import pytest
import tempfile
import shutil
from datetime import datetime

# Ensure the code directory is in the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from t040_create_comparison_report import (
    load_baseline_metrics,
    load_cleaned_metrics,
    aggregate_metrics_for_comparison,
    create_comparison_report
)
from models import ComparisonReport

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_aggregate_metrics_for_comparison(temp_data_dir):
    """Test the aggregation logic with mock data."""
    baseline_data = {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "analysis": {
                    "t_test": {"p_value": 0.03, "ci_width": 0.1, "effect_size": 0.5},
                    "regression": {"r_squared": 0.6}
                }
            }
        ]
    }

    cleaned_data = {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "strategy": "outlier_removal",
                "analysis": {
                    "t_test": {"p_value": 0.01, "ci_width": 0.08, "effect_size": 0.6},
                    "regression": {"r_squared": 0.65}
                }
            }
        ]
    }

    result = aggregate_metrics_for_comparison(baseline_data, cleaned_data)
    
    assert len(result) == 1
    assert result[0]["dataset_name"] == "test_dataset_1"
    assert len(result[0]["cleaned_variants"]) == 1
    assert result[0]["cleaned_variants"][0]["strategy"] == "outlier_removal"
    
    metrics = result[0]["cleaned_variants"][0]["metrics"]
    assert metrics["p_value_shift"] == pytest.approx(0.02, abs=1e-5) # |0.01 - 0.03|
    assert metrics["absolute_diff_p"] == pytest.approx(0.02, abs=1e-5)

def test_create_comparison_report_writes_file(temp_data_dir):
    """Test that the report is written to disk and is valid JSON."""
    baseline_path = os.path.join(temp_data_dir, "baseline.json")
    cleaned_path = os.path.join(temp_data_dir, "cleaned.json")
    output_path = os.path.join(temp_data_dir, "report.json")

    baseline_data = {"datasets": [{"dataset_name": "d1", "analysis": {"t_test": {"p_value": 0.05}}}]}
    cleaned_data = {"datasets": [{"dataset_name": "d1", "strategy": "test", "analysis": {"t_test": {"p_value": 0.04}}}]}

    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)
    with open(cleaned_path, 'w') as f:
        json.dump(cleaned_data, f)

    # Patch the load functions to use our temp paths
    import t040_create_comparison_report as t040_module
    original_load_base = t040_module.load_baseline_metrics
    original_load_clean = t040_module.load_cleaned_metrics

    t040_module.load_baseline_metrics = lambda fp=baseline_path: load_baseline_metrics(fp)
    t040_module.load_cleaned_metrics = lambda fp=cleaned_path: load_cleaned_metrics(fp)

    try:
        report = create_comparison_report(
            baseline_data, cleaned_data, output_path=output_path
        )
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        assert "report_id" in saved_report
        assert "summary" in saved_report
        assert "detailed_comparisons" in saved_report
        assert saved_report["summary"]["total_datasets_analyzed"] == 1
    finally:
        t040_module.load_baseline_metrics = original_load_base
        t040_module.load_cleaned_metrics = original_load_clean

def test_comparison_report_entity_creation():
    """Test that the ComparisonReport Pydantic model is created correctly."""
    baseline = {"datasets": []}
    cleaned = {"datasets": []}
    
    report = ComparisonReport(
        report_id="TEST-001",
        baseline_metrics=baseline,
        cleaned_metrics=cleaned,
        absolute_diff=0.05,
        relative_diff=1.0,
        sensitivity_analysis=None
    )
    
    assert report.report_id == "TEST-001"
    assert report.absolute_diff == 0.05
    assert report.relative_diff == 1.0