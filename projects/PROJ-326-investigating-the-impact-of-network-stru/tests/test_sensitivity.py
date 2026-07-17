"""
Tests for the sensitivity sweep analysis module.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

from code.src.analysis.sensitivity import (
    load_simulation_data,
    filter_by_clustering_threshold,
    compute_sensitivity_metrics,
    run_sensitivity_sweep,
    save_sensitivity_results,
    main
)


@pytest.fixture
def sample_simulation_data():
    """Create sample simulation data for testing."""
    data = [
        {
            "network_id": "net_001",
            "seed": 42,
            "diffusion_rate": 0.85,
            "spatial_variance": 0.12,
            "final_energy_density": 0.55,
            "clustering_coefficient": 0.35,
            "topology_class": "ErdosRenyi"
        },
        {
            "network_id": "net_002",
            "seed": 43,
            "diffusion_rate": 0.72,
            "spatial_variance": 0.18,
            "final_energy_density": 0.62,
            "clustering_coefficient": 0.65,
            "topology_class": "WattsStrogatz"
        },
        {
            "network_id": "net_003",
            "seed": 44,
            "diffusion_rate": 0.91,
            "spatial_variance": 0.09,
            "final_energy_density": 0.48,
            "clustering_coefficient": 0.15,
            "topology_class": "BarabasiAlbert"
        },
        {
            "network_id": "net_004",
            "seed": 45,
            "diffusion_rate": 0.68,
            "spatial_variance": 0.22,
            "final_energy_density": 0.71,
            "clustering_coefficient": 0.78,
            "topology_class": "WattsStrogatz"
        },
        {
            "network_id": "net_005",
            "seed": 46,
            "diffusion_rate": 0.79,
            "spatial_variance": 0.15,
            "final_energy_density": 0.58,
            "clustering_coefficient": 0.42,
            "topology_class": "ErdosRenyi"
        },
    ]
    return pd.DataFrame(data)


@pytest.fixture
def temp_results_file(sample_simulation_data):
    """Create a temporary simulation results file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(sample_simulation_data.to_dict(orient="records"), f)
        return Path(f.name)


def test_load_simulation_data_valid(temp_results_file):
    """Test loading valid simulation data."""
    df = load_simulation_data(temp_results_file)
    assert len(df) == 5
    assert "diffusion_rate" in df.columns
    assert "clustering_coefficient" in df.columns


def test_load_simulation_data_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_simulation_data(Path("nonexistent/file.json"))


def test_filter_by_clustering_threshold(sample_simulation_data):
    """Test filtering by clustering threshold."""
    filtered = filter_by_clustering_threshold(
        sample_simulation_data, threshold=0.5
    )
    # Should only keep records with clustering >= 0.5
    assert len(filtered) == 2
    assert all(filtered["clustering_coefficient"] >= 0.5)


def test_filter_by_clustering_threshold_invalid_column(sample_simulation_data):
    """Test filtering with invalid column name."""
    with pytest.raises(ValueError):
        filter_by_clustering_threshold(
            sample_simulation_data,
            threshold=0.5,
            clustering_col="invalid_column"
        )


def test_compute_sensitivity_metrics(sample_simulation_data):
    """Test computing metrics for a threshold."""
    metrics = compute_sensitivity_metrics(sample_simulation_data, threshold=0.0)
    assert metrics["sample_size"] == 5
    assert "mean_diffusion_rate" in metrics
    assert "std_diffusion_rate" in metrics
    assert "topology_counts" in metrics
    assert len(metrics["topology_counts"]) > 0


def test_compute_sensitivity_metrics_empty_df():
    """Test metrics computation on empty DataFrame."""
    empty_df = pd.DataFrame(columns=["diffusion_rate", "clustering_coefficient"])
    metrics = compute_sensitivity_metrics(empty_df, threshold=1.0)
    assert metrics["sample_size"] == 0
    assert metrics["mean_diffusion_rate"] is None


def test_run_sensitivity_sweep(sample_simulation_data):
    """Test running a full sensitivity sweep."""
    thresholds = [0.0, 0.4, 0.7]
    results = run_sensitivity_sweep(sample_simulation_data, thresholds=thresholds)

    assert len(results) == 3
    assert all(r["threshold"] in thresholds for r in results)
    assert all("sample_size" in r for r in results)
    assert results[0]["sample_size"] == 5  # threshold 0.0 includes all
    assert results[1]["sample_size"] == 3  # threshold 0.4
    assert results[2]["sample_size"] == 1  # threshold 0.7


def test_run_sensitivity_sweep_default_thresholds(sample_simulation_data):
    """Test that default thresholds are used when not specified."""
    results = run_sensitivity_sweep(sample_simulation_data)
    expected_thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]
    assert len(results) == 5
    assert [r["threshold"] for r in results] == expected_thresholds


def test_save_sensitivity_results(tmp_path):
    """Test saving sensitivity results to a file."""
    results = [
        {"threshold": 0.0, "sample_size": 10, "mean_diffusion_rate": 0.5},
        {"threshold": 0.2, "sample_size": 8, "mean_diffusion_rate": 0.55},
        {"threshold": 0.4, "sample_size": 6, "mean_diffusion_rate": 0.6},
        {"threshold": 0.6, "sample_size": 4, "mean_diffusion_rate": 0.65},
        {"threshold": 0.8, "sample_size": 2, "mean_diffusion_rate": 0.7},
    ]

    output_path = tmp_path / "sensitivity_sweep.json"
    saved_path = save_sensitivity_results(results, output_path)

    assert saved_path.exists()
    with open(saved_path, "r") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "results" in data
    assert data["metadata"]["num_thresholds"] == 5
    assert len(data["results"]) == 5


def test_save_sensitivity_results_fewer_than_5_thresholds(tmp_path):
    """Test that saving with <5 thresholds raises ValueError (SC-005)."""
    results = [
        {"threshold": 0.0, "sample_size": 10, "mean_diffusion_rate": 0.5},
        {"threshold": 0.4, "sample_size": 6, "mean_diffusion_rate": 0.6},
    ]

    output_path = tmp_path / "sensitivity_sweep.json"
    with pytest.raises(ValueError, match="SC-005 violation"):
        save_sensitivity_results(results, output_path)


def test_save_sensitivity_results_empty_results(tmp_path):
    """Test that saving empty results raises ValueError."""
    output_path = tmp_path / "sensitivity_sweep.json"
    with pytest.raises(ValueError, match="Cannot save empty"):
        save_sensitivity_results([], output_path)


def test_main_success(sample_simulation_data, tmp_path):
    """Test main function with valid data."""
    # Create a temporary results file
    results_file = tmp_path / "simulation_results.json"
    with open(results_file, "w") as f:
        json.dump(sample_simulation_data.to_dict(orient="records"), f)

    # Patch the load path
    with patch("code.src.analysis.sensitivity.Path") as mock_path:
        mock_path.return_value = tmp_path
        with patch("code.src.analysis.sensitivity.load_simulation_data") as mock_load:
            mock_load.return_value = sample_simulation_data
            with patch("code.src.analysis.sensitivity.save_sensitivity_results") as mock_save:
                mock_save.return_value = tmp_path / "sensitivity_sweep.json"
                result = main()
                assert result == 0


def test_main_file_not_found():
    """Test main function when data file is missing."""
    with patch("code.src.analysis.sensitivity.load_simulation_data") as mock_load:
        mock_load.side_effect = FileNotFoundError("Missing file")
        result = main()
        assert result == 1


def test_main_value_error():
    """Test main function when validation fails."""
    with patch("code.src.analysis.sensitivity.load_simulation_data") as mock_load:
        mock_load.return_value = pd.DataFrame()  # Empty data
        with patch("code.src.analysis.sensitivity.run_sensitivity_sweep") as mock_sweep:
            mock_sweep.return_value = []  # Empty results
            with patch("code.src.analysis.sensitivity.save_sensitivity_results") as mock_save:
                mock_save.side_effect = ValueError("Validation failed")
                result = main()
                assert result == 1
