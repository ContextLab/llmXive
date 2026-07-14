"""
Integration test for T040: Create comparison report.
Verifies that the comparison report is generated correctly with all required fields.
"""
import os
import json
import pytest
from pathlib import Path

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models import ComparisonReport
from t040_create_comparison_report import (
    load_baseline_metrics,
    load_cleaned_metrics,
    load_sensitivity_analysis,
    calculate_absolute_diff,
    calculate_relative_diff,
    aggregate_metrics_for_comparison,
    create_comparison_report,
    main
)
from config import Config

@pytest.fixture
def sample_baseline_metrics():
    return {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "p_value": 0.045,
                "ci_width": 0.15,
                "effect_size": 0.5,
                "n_rows": 100,
                "analysis": {
                    "t_test": {"p_value": 0.045, "ci": [0.4, 0.55]},
                    "regression": {"r_squared": 0.3, "coefficients": [1.2]}
                }
            }
        ]
    }

@pytest.fixture
def sample_cleaned_metrics():
    return {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "cleaning_strategy": "iqr_outlier",
                "p_value": 0.032,
                "ci_width": 0.12,
                "effect_size": 0.6,
                "n_rows": 95,
                "analysis": {
                    "t_test": {"p_value": 0.032, "ci": [0.45, 0.57]},
                    "regression": {"r_squared": 0.35, "coefficients": [1.3]}
                }
            }
        ]
    }

@pytest.fixture
def sample_sensitivity_analysis():
    return {
        "status": "complete",
        "bins": {
            "small": {"count": 1, "avg_shift": 0.01},
            "medium": {"count": 0, "avg_shift": 0.0},
            "large": {"count": 0, "avg_shift": 0.0}
        },
        "bootstrap_results": {"mean_shift": 0.015, "ci": [0.01, 0.02]}
    }

def test_calculate_absolute_diff():
    assert calculate_absolute_diff(0.05, 0.03) == 0.02
    assert calculate_absolute_diff(0.05, 0.05) == 0.0
    assert calculate_absolute_diff(None, 0.03) == 0.0

def test_calculate_relative_diff():
    assert abs(calculate_relative_diff(0.05, 0.03) - 0.4) < 0.001
    assert calculate_relative_diff(0.05, 0.05) == 0.0
    assert calculate_relative_diff(0.0, 0.03) == 0.0
    assert calculate_relative_diff(None, 0.03) == 0.0

def test_aggregate_metrics_for_comparison(sample_baseline_metrics, sample_cleaned_metrics):
    result = aggregate_metrics_for_comparison(sample_baseline_metrics, sample_cleaned_metrics)
    
    assert "baseline_datasets" in result
    assert "cleaned_datasets" in result
    assert "comparisons" in result
    
    assert len(result["baseline_datasets"]) == 1
    assert len(result["cleaned_datasets"]) == 1
    assert len(result["comparisons"]) == 1
    
    comp = result["comparisons"][0]
    assert comp["dataset_name"] == "test_dataset_1"
    assert comp["cleaning_strategy"] == "iqr_outlier"
    assert "metrics" in comp
    assert "p_value" in comp["metrics"]
    assert "absolute_diff" in comp["metrics"]["p_value"]
    assert "relative_diff" in comp["metrics"]["p_value"]

def test_create_comparison_report_entity(sample_baseline_metrics, sample_cleaned_metrics, sample_sensitivity_analysis):
    report = create_comparison_report(
        sample_baseline_metrics,
        sample_cleaned_metrics,
        sample_sensitivity_analysis
    )
    
    assert isinstance(report, ComparisonReport)
    assert report.baseline_metrics is not None
    assert report.cleaned_metrics is not None
    assert report.absolute_diff is not None
    assert report.relative_diff is not None
    assert report.sensitivity_analysis is not None
    assert report.summary is not None
    assert "total_comparisons" in report.summary
    assert report.created_at is not None

def test_main_execution(tmp_path, sample_baseline_metrics, sample_cleaned_metrics, sample_sensitivity_analysis):
    # Setup mock files
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    baseline_file = processed_dir / "baseline_metrics.json"
    cleaned_file = processed_dir / "cleaned_metrics.json"
    sensitivity_file = processed_dir / "sensitivity_analysis.json"
    
    with open(baseline_file, 'w') as f:
        json.dump(sample_baseline_metrics, f)
    with open(cleaned_file, 'w') as f:
        json.dump(sample_cleaned_metrics, f)
    with open(sensitivity_file, 'w') as f:
        json.dump(sample_sensitivity_analysis, f)
    
    # Mock config to use tmp_path
    original_get = Config.get
    def mock_get(self, key, default=None):
        if key == "PROCESSED_DATA_PATH":
            return str(processed_dir)
        return original_get(self, key, default)
    
    Config.get = mock_get
    
    try:
        exit_code = main()
        assert exit_code == 0
        
        output_file = processed_dir / "comparison_report.json"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "baseline_metrics" in data
        assert "cleaned_metrics" in data
        assert "absolute_diff" in data
        assert "relative_diff" in data
        assert "sensitivity_analysis" in data
        assert "summary" in data
    finally:
        Config.get = original_get

def test_missing_baseline_file(tmp_path, caplog):
    # Setup empty processed dir
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Mock config
    original_get = Config.get
    def mock_get(self, key, default=None):
        if key == "PROCESSED_DATA_PATH":
            return str(processed_dir)
        return original_get(self, key, default)
    
    Config.get = mock_get
    
    try:
        exit_code = main()
        assert exit_code != 0
        assert "Missing required data file" in caplog.text
    finally:
        Config.get = original_get