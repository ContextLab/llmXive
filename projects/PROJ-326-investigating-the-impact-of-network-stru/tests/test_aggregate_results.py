"""
Unit tests for the aggregate_results module.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from code.src.analysis.aggregate_results import (
    load_simulation_results,
    filter_valid_runs,
    aggregate_metrics,
    aggregate_results,
    STATUS_EXCLUDED
)


@pytest.fixture
def sample_results(tmp_path):
    """Create a temporary file with sample simulation results."""
    data = [
        {"network_id": "1", "diffusion_rate": 0.5, "status": "SUCCESS", "topology_class": "ErdosRenyi"},
        {"network_id": "2", "diffusion_rate": 0.6, "status": "SUCCESS", "topology_class": "WattsStrogatz"},
        {"network_id": "3", "diffusion_rate": np.nan, "status": "[SIMULATION_DIVERGENCE]", "topology_class": "BarabasiAlbert"},
        {"network_id": "4", "diffusion_rate": 0.4, "status": "[DISCONNECTED_NETWORK_FAILURE]", "topology_class": "ErdosRenyi"},
        {"network_id": "5", "diffusion_rate": 0.7, "status": "SUCCESS", "topology_class": "WattsStrogatz"},
    ]
    file_path = tmp_path / "simulation_results.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return str(file_path)


def test_load_simulation_results(sample_results):
    """Test loading simulation results from JSON."""
    df = load_simulation_results(sample_results)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert "diffusion_rate" in df.columns
    assert "status" in df.columns


def test_filter_valid_runs(sample_results):
    """Test filtering out excluded status runs."""
    df = load_simulation_results(sample_results)
    valid_df, excluded_count = filter_valid_runs(df)

    assert excluded_count == 2
    assert len(valid_df) == 3
    # Check that no excluded statuses remain
    for status in valid_df['status']:
        assert status not in STATUS_EXCLUDED


def test_aggregate_metrics(sample_results):
    """Test aggregation of numeric metrics."""
    df = load_simulation_results(sample_results)
    valid_df, _ = filter_valid_runs(df)
    metrics = aggregate_metrics(valid_df)

    assert "diffusion_rate" in metrics
    assert metrics["diffusion_rate"]["count"] == 3
    # Mean of 0.5, 0.6, 0.7 is 0.6
    assert np.isclose(metrics["diffusion_rate"]["mean"], 0.6)
    assert metrics["diffusion_rate"]["median"] == 0.6


def test_aggregate_results_full_flow(sample_results, tmp_path):
    """Test the full aggregation flow."""
    output_path = str(tmp_path / "aggregated_results.json")
    result = aggregate_results(sample_results, output_path)

    assert os.path.exists(output_path)
    assert result["total_input_records"] == 5
    assert result["valid_records"] == 3
    assert result["excluded_records"] == 2
    assert result["status"] == "SUCCESS"

    # Verify file content
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    assert "aggregated_metrics" in saved_data
    assert "topology_specific_metrics" in saved_data


def test_aggregate_results_empty_after_filter(tmp_path):
    """Test behavior when all records are filtered out."""
    # Create data where all are excluded
    data = [
        {"network_id": "1", "status": "[SIMULATION_DIVERGENCE]"},
        {"network_id": "2", "status": "[DISCONNECTED_NETWORK_FAILURE]"},
    ]
    input_path = tmp_path / "simulation_results.json"
    with open(input_path, 'w') as f:
        json.dump(data, f)

    output_path = tmp_path / "aggregated_results.json"

    with pytest.raises(ValueError, match="No valid runs found"):
        aggregate_results(str(input_path), str(output_path))