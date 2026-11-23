"""
Unit tests for threshold_fit_params module (Task T022c).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from analysis.threshold_fit_params import write_fit_parameters, load_fitted_parameters
from utils.config import get_project_paths


@pytest.fixture
def mock_mc_data():
    """Mock Monte Carlo data for testing."""
    return [
        {"run_id": "1", "N": 1000, "theta": 1.5, "seed": 42, "outlier_count": 0, "max_eigenvalue": 1.95},
        {"run_id": "2", "N": 1000, "theta": 1.5, "seed": 43, "outlier_count": 0, "max_eigenvalue": 1.98},
        {"run_id": "3", "N": 1000, "theta": 2.0, "seed": 44, "outlier_count": 5, "max_eigenvalue": 2.05},
        {"run_id": "4", "N": 1000, "theta": 2.0, "seed": 45, "outlier_count": 6, "max_eigenvalue": 2.10},
        {"run_id": "5", "N": 1000, "theta": 2.5, "seed": 46, "outlier_count": 10, "max_eigenvalue": 2.55},
    ]


@pytest.fixture
def mock_aggregated_data():
    """Mock aggregated data for testing."""
    return {
        1.5: {"total": 2, "outliers": 0, "prob": 0.0},
        2.0: {"total": 2, "outliers": 11, "prob": 0.55},
        2.5: {"total": 2, "outliers": 20, "prob": 1.0},
    }


@pytest.fixture
def mock_fit_result():
    """Mock fit result."""
    return {
        "theta_c": 1.95,
        "slope": 2.5,
        "r_squared": 0.98,
        "message": "Fit successful"
    }


def test_load_fitted_parameters_success(mock_mc_data, mock_aggregated_data, mock_fit_result):
    """Test that load_fitted_parameters correctly processes data and returns fit results."""
    with patch("analysis.threshold_fit_params.load_mc_results") as mock_load, \
         patch("analysis.threshold_fit_params.aggregate_by_theta") as mock_agg, \
         patch("analysis.threshold_fit_params.fit_critical_threshold") as mock_fit:

        mock_load.return_value = mock_mc_data
        mock_agg.return_value = mock_aggregated_data
        mock_fit.return_value = mock_fit_result

        result = load_fitted_parameters()

        assert result == mock_fit_result
        mock_load.assert_called_once()
        mock_agg.assert_called_once()
        mock_fit.assert_called_once()


def test_write_fit_parameters_creates_file(mock_mc_data, mock_aggregated_data, mock_fit_result):
    """Test that write_fit_parameters creates the JSON file with correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_params.json"

        with patch("analysis.threshold_fit_params.load_fitted_parameters") as mock_load:
            mock_load.return_value = mock_fit_result

            result_path = write_fit_parameters(output_path)

            assert result_path.exists()
            assert result_path == output_path

            with open(result_path, "r") as f:
                data = json.load(f)

            assert "theta_c" in data
            assert "slope" in data
            assert "generated_at" in data
            assert data["theta_c"] == 1.95


def test_write_fit_parameters_missing_mc_results():
    """Test that write_fit_parameters raises error if mc_results.csv is missing."""
    with patch("utils.config.get_project_paths") as mock_paths:
        mock_paths.return_value = {"data_processed": Path("/nonexistent")}

        with pytest.raises(FileNotFoundError):
            write_fit_parameters()


def test_write_fit_parameters_empty_data():
    """Test that write_fit_parameters raises error if data is empty."""
    with patch("analysis.threshold_fit_params.load_mc_results") as mock_load, \
         patch("analysis.threshold_fit_params.aggregate_by_theta") as mock_agg:

        mock_load.return_value = []
        mock_agg.return_value = {}

        with pytest.raises(ValueError):
            write_fit_parameters()


def test_write_fit_parameters_fitting_fails(mock_mc_data, mock_aggregated_data):
    """Test that write_fit_parameters raises error if fitting fails."""
    with patch("analysis.threshold_fit_params.load_mc_results") as mock_load, \
         patch("analysis.threshold_fit_params.aggregate_by_theta") as mock_agg, \
         patch("analysis.threshold_fit_params.fit_critical_threshold") as mock_fit:

        mock_load.return_value = mock_mc_data
        mock_agg.return_value = mock_aggregated_data
        mock_fit.return_value = None

        with pytest.raises(RuntimeError):
            write_fit_parameters()