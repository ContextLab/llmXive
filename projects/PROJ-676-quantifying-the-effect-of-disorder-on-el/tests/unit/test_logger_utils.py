"""
Unit tests for logger_utils module.

Tests that residuals and convergence flags are correctly logged.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from code.logger_utils import log_eigenvalue_residual, _append_to_residuals_json, get_logger
from code.config import get_config


@pytest.fixture
def mock_config(tmp_path):
    """Fixture to mock config paths to a temporary directory."""
    mock_cfg = {
        'DATA_DIR': str(tmp_path),
        'DATA_METADATA': str(tmp_path / "metadata"),
    }
    with patch('code.logger_utils.get_config', return_value=mock_cfg):
        with patch('code.config.get_config', return_value=mock_cfg):
            yield tmp_path


def test_log_eigenvalue_residual_success(mock_config):
    """Test logging of a successful eigenvalue solve."""
    system_params = {'W': 1.0, 'L': 100, 'realization_index': 0, 'seed': 42}
    eigenvalues = [0.1, 0.2, 0.3]
    eigenvectors = np.eye(3)
    residuals = [1e-10, 1e-10, 1e-10]
    converged = [True, True, True]

    log_eigenvalue_residual(system_params, eigenvalues, eigenvectors, residuals, converged)

    # Check that the file was created
    residuals_file = Path(mock_config) / "metadata" / "residuals.json"
    assert residuals_file.exists()

    with open(residuals_file, 'r') as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]['system']['W'] == 1.0
    assert data[0]['summary']['all_converged'] is True
    assert data[0]['summary']['max_residual'] == 1e-10


def test_log_eigenvalue_residual_failure(mock_config):
    """Test logging of a failed eigenvalue solve."""
    system_params = {'W': 5.0, 'L': 100, 'realization_index': 1, 'seed': 43}
    eigenvalues = [0.1, 0.2, 0.3]
    eigenvectors = np.eye(3)
    residuals = [1e-2, 1e-10, 1e-10]
    converged = [False, True, True]

    log_eigenvalue_residual(system_params, eigenvalues, eigenvectors, residuals, converged)

    residuals_file = Path(mock_config) / "metadata" / "residuals.json"
    with open(residuals_file, 'r') as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]['summary']['all_converged'] is False
    # Details should be present because not all converged
    assert data[0]['details'] is not None
    assert len(data[0]['details']) == 3
    assert data[0]['details'][0]['converged'] is False


def test_append_to_residuals_json_existing_data(mock_config):
    """Test appending to an existing JSON file."""
    # Create initial data
    initial_entry = {
        "timestamp": "2023-01-01T00:00:00",
        "solver": "test",
        "system": {"W": 0.1},
        "summary": {"all_converged": True},
        "details": None
    }
    residuals_file = Path(mock_config) / "metadata" / "residuals.json"
    residuals_file.parent.mkdir(parents=True, exist_ok=True)
    with open(residuals_file, 'w') as f:
        json.dump([initial_entry], f)

    # Append new entry
    new_entry = {
        "timestamp": "2023-01-02T00:00:00",
        "solver": "test",
        "system": {"W": 0.2},
        "summary": {"all_converged": True},
        "details": None
    }
    _append_to_residuals_json(new_entry)

    with open(residuals_file, 'r') as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[1]['system']['W'] == 0.2