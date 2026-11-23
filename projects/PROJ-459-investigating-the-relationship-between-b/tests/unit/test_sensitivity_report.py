"""
Unit tests for sensitivity_report.py
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

from analysis.sensitivity_report import generate_sensitivity_report, main
from config import get_derived_path
from utils.io import save_json

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_metrics():
    # Simulated output from T026
    return {
        20: {"global_efficiency": 0.45, "modularity": 0.32},
        30: {"global_efficiency": 0.46, "modularity": 0.31},
        40: {"global_efficiency": 0.44, "modularity": 0.33}
    }

@pytest.fixture
def sample_icc():
    # Simulated output from T027
    return {
        "global_efficiency": 0.82,
        "modularity": 0.65
    }

def test_generate_sensitivity_report_structure(sample_metrics, sample_icc, temp_output_dir):
    """Test that the generated report has the correct structure."""
    output_path = temp_output_dir / "sensitivity_report.json"
    
    report = generate_sensitivity_report(
        sample_metrics, 
        sample_icc, 
        output_path=output_path
    )
    
    assert "analysis_type" in report
    assert report["analysis_type"] == "sensitivity_analysis"
    assert "window_sizes_analyzed" in report
    assert sorted(report["window_sizes_analyzed"]) == [20, 30, 40]
    assert "stability_metrics" in report
    assert "icc_results" in report
    
    # Check stability metrics
    assert "global_efficiency" in report["stability_metrics"]
    ge_stability = report["stability_metrics"]["global_efficiency"]
    assert "mean" in ge_stability
    assert "std" in ge_stability
    assert "cv" in ge_stability
    
    # Check ICC results
    assert len(report["icc_results"]) == 2
    icc_dict = {item["metric"]: item for item in report["icc_results"]}
    assert abs(icc_dict["global_efficiency"]["icc"] - 0.82) < 0.01
    assert icc_dict["global_efficiency"]["stability_category"] == "stable"
    
    # Check file existence
    assert output_path.exists()
    
    # Check Parquet file existence
    parquet_path = output_path.with_suffix(".parquet")
    assert parquet_path.exists()
    df = pd.read_parquet(parquet_path)
    assert "window_size" in df.columns
    assert "metric_name" in df.columns
    assert "value" in df.columns

def test_generate_sensitivity_report_single_window(sample_metrics, sample_icc, temp_output_dir):
    """Test behavior with only one window size (no stability calc)."""
    single_window_metrics = {30: {"global_efficiency": 0.46}}
    output_path = temp_output_dir / "single_report.json"
    
    report = generate_sensitivity_report(
        single_window_metrics, 
        sample_icc, 
        output_path=output_path
    )
    
    # Should not crash, but stability metrics might be empty or have zero variance logic
    # depending on implementation. Here we just ensure it runs.
    assert "stability_metrics" in report
    
@patch('analysis.sensitivity_report.get_derived_path')
@patch('analysis.sensitivity_report.load_json')
@patch('analysis.sensitivity_report.save_json')
def test_main_flow(mock_save, mock_load, mock_get_path, sample_metrics, sample_icc, temp_output_dir):
    """Test the main() function flow."""
    metrics_path = temp_output_dir / "sensitivity_metrics.json"
    icc_path = temp_output_dir / "icc_results.json"
    report_path = temp_output_dir / "final_report.json"
    
    # Setup mocks
    mock_get_path.side_effect = lambda name: {
        "sensitivity_metrics.json": metrics_path,
        "icc_results.json": icc_path,
        "sensitivity_report.json": report_path
    }[name]
    
    mock_load.side_effect = lambda path: sample_metrics if "metrics" in str(path) else sample_icc
    
    # Run main
    result = main()
    
    # Verify save was called
    assert mock_save.called
    assert result is not None

def test_missing_intermediate_files(temp_output_dir):
    """Test that main() raises error if intermediate files are missing."""
    with patch('analysis.sensitivity_report.get_derived_path') as mock_path:
        mock_path.return_value = temp_output_dir / "nonexistent.json"
        mock_path.side_effect = lambda name: temp_output_dir / name
        
        with pytest.raises(FileNotFoundError):
            main()
