"""
Unit tests for the visualization module (T032).
"""
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
import json

from code.analysis.visualize import plot_sampling_rate_vs_bias

@pytest.fixture
def mock_metrics_data():
    """Generate mock metrics data for testing."""
    return [
        {
            "event_id": "GW150914",
            "sampling_rate": 4096,
            "bias_magnitude": 0.01,
            "catalog_uncertainty": 0.05
        },
        {
            "event_id": "GW150914",
            "sampling_rate": 2048,
            "bias_magnitude": 0.03,
            "catalog_uncertainty": 0.05
        },
        {
            "event_id": "GW150914",
            "sampling_rate": 1024,
            "bias_magnitude": 0.12,
            "catalog_uncertainty": 0.05
        }
    ]

@pytest.fixture
def temp_results_dir(mock_metrics_data):
    """Create a temporary directory with mock metric files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = Path(tmpdir)
        # Create a mock aggregation report
        report = {
            "metrics": mock_metrics_data
        }
        with open(results_path / "aggregation_report.json", 'w') as f:
            json.dump(report, f)
        yield results_path

def test_plot_generation_single_event(temp_results_dir, tmp_path):
    """Test that a plot is generated for a single event."""
    output_file = tmp_path / "test_plot.png"
    
    # This should not raise an exception
    result_path = plot_sampling_rate_vs_bias(temp_results_dir, output_file, event_id="GW150914")
    
    assert result_path.exists()
    assert result_path.suffix == ".png"
    assert result_path.stat().st_size > 0

def test_plot_generation_no_metrics(tmp_path):
    """Test handling of empty metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = Path(tmpdir)
        # Create empty report
        with open(results_path / "aggregation_report.json", 'w') as f:
            json.dump({"metrics": []}, f)
        
        output_file = tmp_path / "empty_plot.png"
        result_path = plot_sampling_rate_vs_bias(results_path, output_file)
        
        assert result_path.exists()
        # Should contain a warning message
        # (We can't easily check text content of a PNG without OCR, 
        # but we verify it was created and isn't empty)
        assert result_path.stat().st_size > 0

def test_plot_generation_multiple_events(tmp_path):
    """Test plotting multiple events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = Path(tmpdir)
        multi_data = [
            {"event_id": "GW150914", "sampling_rate": 4096, "bias_magnitude": 0.01, "catalog_uncertainty": 0.05},
            {"event_id": "GW150914", "sampling_rate": 2048, "bias_magnitude": 0.03, "catalog_uncertainty": 0.05},
            {"event_id": "GW151226", "sampling_rate": 4096, "bias_magnitude": 0.02, "catalog_uncertainty": 0.06},
            {"event_id": "GW151226", "sampling_rate": 2048, "bias_magnitude": 0.04, "catalog_uncertainty": 0.06},
        ]
        with open(results_path / "aggregation_report.json", 'w') as f:
            json.dump({"metrics": multi_data}, f)
        
        output_file = tmp_path / "multi_plot.png"
        result_path = plot_sampling_rate_vs_bias(results_path, output_file)
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0