"""
Unit tests for the aggregator module (T032).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the module under test
# Note: We assume the analysis module is in the code/ directory
# and we are running tests from the project root or with PYTHONPATH set
from analysis.aggregator import aggregate_results, generate_final_pareto

@pytest.fixture
def sample_latency_data():
    """Create sample latency data for testing."""
    data = [
        {"config_id": "cfg_001", "kernel_type": "matmul", "median": 0.001, "p95": 0.0012, "iterations": 1000},
        {"config_id": "cfg_002", "kernel_type": "matmul", "median": 0.0009, "p95": 0.0011, "iterations": 1000},
        {"config_id": "cfg_003", "kernel_type": "softmax", "median": 0.0005, "p95": 0.0006, "iterations": 1000},
    ]
    return pd.DataFrame(data)

@pytest.fixture
def sample_stability_data():
    """Create sample stability metrics for testing."""
    data = [
        {"config_id": "cfg_001", "kernel_type": "matmul", "l2_error": 1e-6, "max_diff": 5e-6, "status": "stable"},
        {"config_id": "cfg_002", "kernel_type": "matmul", "l2_error": 1e-4, "max_diff": 2e-4, "status": "unstable"},
        {"config_id": "cfg_003", "kernel_type": "softmax", "l2_error": 1e-7, "max_diff": 3e-7, "status": "stable"},
    ]
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_aggregate_results_creates_csv(sample_latency_data, sample_stability_data, temp_dir):
    """Test that aggregate_results creates a valid CSV file."""
    # Write sample data to temporary files
    latency_file = Path(temp_dir) / "latency.jsonl"
    stability_file = Path(temp_dir) / "stability.csv"
    output_file = Path(temp_dir) / "aggregated.csv"
    
    sample_latency_data.to_json(latency_file, orient='records', lines=True)
    sample_stability_data.to_csv(stability_file, index=False)
    
    # Run aggregation
    result_df = aggregate_results(
        latency_data_path=str(latency_file),
        stability_metrics_path=str(stability_file),
        output_csv_path=str(output_file)
    )
    
    # Assertions
    assert not result_df.empty
    assert "config_id" in result_df.columns
    assert "median" in result_df.columns
    assert "max_diff" in result_df.columns
    assert output_file.exists()
    
    # Verify the merged data
    assert len(result_df) == 3  # All 3 configs should merge
    # Check that unstable config (cfg_002) is included in CSV but marked
    unstable_row = result_df[result_df["config_id"] == "cfg_002"]
    assert not unstable_row.empty
    assert unstable_row.iloc[0]["max_diff"] == 2e-4

def test_generate_final_pareto_filters_unstable(sample_latency_data, sample_stability_data, temp_dir):
    """Test that generate_final_pareto excludes unstable configurations."""
    # Write sample data
    latency_file = Path(temp_dir) / "latency.jsonl"
    stability_file = Path(temp_dir) / "stability.csv"
    aggregated_file = Path(temp_dir) / "aggregated.csv"
    plot_file = Path(temp_dir) / "pareto_final.png"
    
    sample_latency_data.to_json(latency_file, orient='records', lines=True)
    sample_stability_data.to_csv(stability_file, index=False)
    
    # Create aggregated CSV manually for this test
    merged = pd.merge(sample_latency_data, sample_stability_data, on=["config_id", "kernel_type"])
    merged.to_csv(aggregated_file, index=False)
    
    # Generate plot
    generate_final_pareto(
        aggregated_csv_path=str(aggregated_file),
        output_plot_path=str(plot_file),
        error_threshold=1e-5
    )
    
    # Assertions
    assert plot_file.exists()
    # The plot should only include stable configs (cfg_001 and cfg_003)
    # cfg_002 has max_diff 2e-4 which is > 1e-5

def test_aggregate_results_handles_missing_data(temp_dir):
    """Test aggregation behavior with missing or empty files."""
    latency_file = Path(temp_dir) / "latency.jsonl"
    stability_file = Path(temp_dir) / "stability.csv"
    output_file = Path(temp_dir) / "aggregated.csv"
    
    # Create empty files
    latency_file.touch()
    stability_file.touch()
    
    # Should return empty DataFrame without crashing
    result_df = aggregate_results(
        latency_data_path=str(latency_file),
        stability_metrics_path=str(stability_file),
        output_csv_path=str(output_file)
    )
    
    assert result_df.empty