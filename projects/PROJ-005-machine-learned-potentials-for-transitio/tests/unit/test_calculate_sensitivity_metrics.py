"""
Unit tests for T017b: calculate_sensitivity_metrics.py
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from src.data.calculate_sensitivity_metrics import (
    load_raw_sensitivity_results,
    calculate_variance_metrics,
    run_sensitivity_metric_calculation
)

@pytest.fixture
def mock_raw_data():
    """Create mock raw sensitivity data with varying cutoffs."""
    return [
        {"cutoff": 3.0, "samples_processed": 100, "total_edges": 500, "graph_density": 0.05, "avg_edge_feature_cv": 0.1, "status": "ok"},
        {"cutoff": 3.5, "samples_processed": 100, "total_edges": 520, "graph_density": 0.052, "avg_edge_feature_cv": 0.12, "status": "ok"},
        {"cutoff": 4.0, "samples_processed": 100, "total_edges": 510, "graph_density": 0.051, "avg_edge_feature_cv": 0.11, "status": "ok"},
    ]

@pytest.fixture
def temp_input_file(mock_raw_data):
    """Create a temporary input file with mock data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_raw_data, f)
        return Path(f.name)

def test_load_raw_sensitivity_results(temp_input_file):
    """Test loading raw sensitivity results from JSON file."""
    data = load_raw_sensitivity_results(temp_input_file)
    assert isinstance(data, list)
    assert len(data) == 3
    assert all("cutoff" in item for item in data)

def test_load_raw_sensitivity_results_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_raw_sensitivity_results(Path("/nonexistent/path.json"))

def test_calculate_variance_metrics(mock_raw_data):
    """Test variance calculation across cutoffs."""
    metrics = calculate_variance_metrics(mock_raw_data)
    
    assert metrics["status"] == "computed"
    assert len(metrics["cutoffs_tested"]) == 3
    assert "metrics" in metrics
    assert "variance" in metrics["metrics"]
    assert "coefficient_of_variation" in metrics["metrics"]
    
    # Check that variance is calculated for all metrics
    variance_keys = ["samples_processed", "total_edges", "graph_density", "avg_edge_feature_cv"]
    for key in variance_keys:
        assert key in metrics["metrics"]["variance"]
        assert isinstance(metrics["metrics"]["variance"][key], float)

def test_calculate_variance_metrics_constant_values():
    """Test variance calculation when values are constant."""
    constant_data = [
        {"cutoff": 3.0, "samples_processed": 100, "total_edges": 500, "graph_density": 0.05, "avg_edge_feature_cv": 0.1, "status": "ok"},
        {"cutoff": 3.5, "samples_processed": 100, "total_edges": 500, "graph_density": 0.05, "avg_edge_feature_cv": 0.1, "status": "ok"},
        {"cutoff": 4.0, "samples_processed": 100, "total_edges": 500, "graph_density": 0.05, "avg_edge_feature_cv": 0.1, "status": "ok"},
    ]
    
    metrics = calculate_variance_metrics(constant_data)
    
    # Variance should be 0 for constant values
    assert metrics["metrics"]["variance"]["samples_processed"] == 0.0
    assert metrics["metrics"]["variance"]["total_edges"] == 0.0
    assert metrics["metrics"]["variance"]["graph_density"] == 0.0

def test_calculate_variance_metrics_no_data():
    """Test handling of all 'no_data' status entries."""
    no_data = [
        {"cutoff": 3.0, "samples_processed": 0, "total_edges": 0, "graph_density": 0.0, "avg_edge_feature_cv": 0.0, "status": "no_data"},
        {"cutoff": 3.5, "samples_processed": 0, "total_edges": 0, "graph_density": 0.0, "avg_edge_feature_cv": 0.0, "status": "no_data"},
    ]
    
    metrics = calculate_variance_metrics(no_data)
    
    assert metrics["status"] == "no_data"
    assert "no data was available" in metrics["message"].lower()

def test_run_sensitivity_metric_calculation(temp_input_file):
    """Test full pipeline from input to output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cutoff_sensitivity.json"
        
        metrics = run_sensitivity_metric_calculation(
            input_path=temp_input_file,
            output_path=output_path
        )
        
        assert output_path.exists()
        assert metrics["status"] == "computed"
        
        # Verify the saved file
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == metrics