"""
Unit tests for sensitivity density sweep functionality (Task T028).
"""

import pytest
import numpy as np
import os
import sys
from pathlib import Path
import csv
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.sensitivity_density_sweep import run_single_density_instance, run_sensitivity_density_sweep
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues
from analysis.outlier_detect import detect_outliers

@pytest.fixture
def mock_generators():
    """Mock the Wigner matrix and perturbation generators for testing."""
    with patch('analysis.sensitivity_density_sweep.generate_wigner_matrix') as mock_wigner, \
         patch('analysis.sensitivity_density_sweep.create_perturbation') as mock_perturb:
        
        # Create a simple 3x3 Wigner matrix for testing
        mock_wigner.return_value = np.array([
            [0.5, 0.2, 0.1],
            [0.2, -0.3, 0.4],
            [0.1, 0.4, 0.2]
        ])
        
        # Create a simple 3x3 perturbation matrix
        mock_perturb.return_value = np.array([
            [2.5, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0]
        ])
        
        yield mock_wigner, mock_perturb

@pytest.fixture
def mock_eigen_solver():
    """Mock the eigenvalue solver."""
    with patch('analysis.sensitivity_density_sweep.compute_top_eigenvalues') as mock_eig:
        # Return some test eigenvalues
        mock_eig.return_value = np.array([2.7, 0.5, -0.3])
        yield mock_eig

@pytest.fixture
def mock_outlier_detect():
    """Mock the outlier detection."""
    with patch('analysis.sensitivity_density_sweep.detect_outliers') as mock_detect:
        mock_result = MagicMock()
        mock_result.outlier_count = 1
        mock_result.has_outlier = True
        mock_detect.return_value = mock_result
        yield mock_detect

def test_run_single_density_instance(mock_generators, mock_eigen_solver, mock_outlier_detect):
    """Test a single density instance run."""
    result = run_single_density_instance(
        N=3,
        density=0.2,
        pattern="diagonal",
        theta=2.5,
        seed=42,
        num_eigenvalues=3
    )
    
    assert "run_id" in result
    assert result["N"] == 3
    assert result["density"] == 0.2
    assert result["pattern"] == "diagonal"
    assert result["theta"] == 2.5
    assert result["seed"] == 42
    assert "max_eigenvalue" in result
    assert "outlier_count" in result
    assert "outlier_flag" in result
    assert result["outlier_flag"] is True

def test_run_sensitivity_density_sweep_creates_csv(tmp_path):
    """Test that the sweep creates the expected CSV file."""
    output_path = tmp_path / "sensitivity_density_sweep.csv"
    
    with patch('analysis.sensitivity_density_sweep.run_single_density_instance') as mock_run:
        # Mock a single result
        mock_run.return_value = {
            "run_id": "test_run",
            "N": 100,
            "density": 0.1,
            "pattern": "diagonal",
            "theta": 2.5,
            "seed": 42,
            "max_eigenvalue": 2.7,
            "outlier_count": 1,
            "outlier_flag": True,
            "bbp_threshold": 2.0,
            "timestamp": "2023-01-01T00:00:00"
        }
        
        results = run_sensitivity_density_sweep(
            output_path=str(output_path),
            N=100,
            densities=[0.1],
            patterns=["diagonal"],
            theta=2.5,
            num_iterations=1,
            base_seed=42
        )
        
        assert len(results) == 1
        assert output_path.exists()
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["density"] == "0.1"
            assert rows[0]["pattern"] == "diagonal"

def test_run_sensitivity_density_sweep_multiple_iterations(tmp_path):
    """Test sweep with multiple iterations."""
    output_path = tmp_path / "sensitivity_density_sweep.csv"
    
    with patch('analysis.sensitivity_density_sweep.run_single_density_instance') as mock_run:
        mock_run.return_value = {
            "run_id": "test_run",
            "N": 100,
            "density": 0.1,
            "pattern": "diagonal",
            "theta": 2.5,
            "seed": 42,
            "max_eigenvalue": 2.7,
            "outlier_count": 1,
            "outlier_flag": True,
            "bbp_threshold": 2.0,
            "timestamp": "2023-01-01T00:00:00"
        }
        
        results = run_sensitivity_density_sweep(
            output_path=str(output_path),
            N=100,
            densities=[0.1],
            patterns=["diagonal"],
            theta=2.5,
            num_iterations=3,
            base_seed=42
        )
        
        assert len(results) == 3
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3