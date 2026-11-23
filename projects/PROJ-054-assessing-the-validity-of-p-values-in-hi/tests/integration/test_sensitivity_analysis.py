"""
Integration tests for T029 Sensitivity Analysis.

These tests verify that the sensitivity analysis script:
1. Correctly loads trajectory data for specific rho values.
2. Calculates KS statistics accurately.
3. Produces the expected output file structure.
4. Handles missing data gracefully (fails loudly).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.exceptions import AnalysisError
from code.sensitivity_analysis import (
    load_trajectories_for_rho,
    calculate_ks_statistic_for_rho,
    run_sensitivity_analysis,
    RHO_VALUES,
    TRAJECTORIES_DIR,
    OUTPUT_FILE
)


@pytest.fixture
def mock_trajectory_dir(tmp_path):
    """Create a temporary directory with mock trajectory files."""
    mock_dir = tmp_path / "synthetic" / "trajectories"
    mock_dir.mkdir(parents=True)

    # Create mock data for rho=0.0
    traj_0 = {
        "rho": 0.0,
        "n": 100,
        "p": 50,
        "seed": 123,
        "p_values": np.random.uniform(0, 1, 100).tolist()
    }
    with open(mock_dir / "seed_123.json", 'w') as f:
        json.dump(traj_0, f)

    # Create mock data for rho=0.5
    traj_1 = {
        "rho": 0.5,
        "n": 100,
        "p": 50,
        "seed": 456,
        "p_values": np.random.uniform(0, 1, 100).tolist()
    }
    with open(mock_dir / "seed_456.json", 'w') as f:
        json.dump(traj_1, f)

    # Create a file with missing p_values (should be skipped)
    bad_traj = {
        "rho": 0.5,
        "n": 100,
        "p": 50,
        "seed": 789,
        "other_key": "data"
    }
    with open(mock_dir / "seed_789.json", 'w') as f:
        json.dump(bad_traj, f)

    return mock_dir.parent


def test_load_trajectories_for_rho(mock_trajectory_dir, monkeypatch):
    """Test that loading trajectories filters by rho correctly."""
    # Monkeypatch the global directory
    monkeypatch.setattr("code.sensitivity_analysis.TRAJECTORIES_DIR", mock_trajectory_dir)

    # Load for rho=0.0
    traject_0 = load_trajectories_for_rho(0.0)
    assert len(traject_0) == 1
    assert len(traject_0[0]) == 100

    # Load for rho=0.5
    traject_05 = load_trajectories_for_rho(0.5)
    assert len(traject_05) == 1  # Only seed_456 is valid, seed_789 skipped
    assert len(traject_05[0]) == 100

    # Load for non-existent rho
    with pytest.raises(AnalysisError):
        load_trajectories_for_rho(0.9)


def test_calculate_ks_statistic_for_rho(mock_trajectory_dir, monkeypatch):
    """Test KS calculation for a specific rho."""
    monkeypatch.setattr("code.sensitivity_analysis.TRAJECTORIES_DIR", mock_trajectory_dir)

    result = calculate_ks_statistic_for_rho(0.0)

    assert result["rho"] == 0.0
    assert "ks_statistics" in result
    assert len(result["ks_statistics"]) == 1
    assert result["mean_ks"] is not None
    assert 0 <= result["mean_ks"] <= 1  # KS stat must be between 0 and 1
    assert result["iteration_count"] == 1


def test_run_sensitivity_analysis(mock_trajectory_dir, monkeypatch):
    """Test the full sensitivity analysis sweep."""
    monkeypatch.setattr("code.sensitivity_analysis.TRAJECTORIES_DIR", mock_trajectory_dir)

    # Mock the output file path to a temp file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_out:
        tmp_path = tmp_out.name

    try:
        # We can't easily monkeypatch the OUTPUT_FILE constant in the function scope
        # without modifying the code, so we test the logic via run_sensitivity_analysis
        # which returns the dict. The file writing is side-effect.

        summary = run_sensitivity_analysis()

        assert "results" in summary
        assert len(summary["results"]) > 0
        assert summary["total_iterations_processed"] >= 2  # At least 2 valid files

        # Check structure of a result item
        first_result = next(r for r in summary["results"] if r["rho"] == 0.0)
        assert "mean_ks" in first_result
        assert first_result["mean_ks"] is not None

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_analysis_fails_loudly_on_missing_data(tmp_path, monkeypatch):
    """Ensure that if no data exists, the analysis raises an error or logs correctly."""
    empty_dir = tmp_path / "synthetic" / "trajectories"
    empty_dir.mkdir(parents=True)

    monkeypatch.setattr("code.sensitivity_analysis.TRAJECTORIES_DIR", empty_dir)

    # This should raise AnalysisError inside calculate_ks_statistic_for_rho
    # or return error status in summary.
    # Based on implementation: load_trajectories_for_rho raises AnalysisError if not found.
    # run_sensitivity_analysis catches it and stores in summary['errors'].

    summary = run_sensitivity_analysis()

    # Check that errors were recorded
    assert len(summary["errors"]) > 0
    assert any(r.get("error") for r in summary["results"])
    # Mean KS should be None for failed items
    assert all(r.get("mean_ks") is None for r in summary["results"] if r.get("error"))