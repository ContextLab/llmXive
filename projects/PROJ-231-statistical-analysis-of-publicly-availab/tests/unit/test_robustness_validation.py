import pytest
import numpy as np
from pathlib import Path
import tempfile
import pickle
import json

# Mock the config to avoid path issues in tests
import sys
from unittest.mock import MagicMock, patch

# We need to mock the config functions or provide them
# Since we can't easily import the real config without the full project structure in this test env,
# we will mock the necessary parts or use a simple local config for testing.

# For this test, we will directly test the logic of run_loo_jackknife
# by mocking the file loading and FPCA execution.

from robustness import run_loo_jackknife, calculate_stability_metrics, procrustes_align

@pytest.fixture
def mock_coefficients_data():
    """Generate mock B-spline coefficients for 5 models."""
    # Shape: (n_models, n_basis, n_timepoints)
    # Let's say 5 models, 10 basis functions, 100 timepoints
    data = {}
    for i in range(5):
        # Create some synthetic but structured data
        timepoints = np.linspace(0, 10, 100)
        coeffs = np.random.randn(10, 100) * 0.1  # Small random noise
        data[f"model_{i}"] = coeffs
    return data

@pytest.fixture
def mock_fpca_results():
    """Generate mock FPCA results."""
    # Eigenfunctions: (n_components, n_timepoints)
    eigenfunctions = np.random.randn(5, 100)
    eigenvalues = np.array([0.5, 0.3, 0.1, 0.05, 0.05])
    return {
        'eigenfunctions': eigenfunctions,
        'eigenvalues': eigenvalues,
        'cumulative_variance': np.cumsum(eigenvalues) / np.sum(eigenvalues)
    }

@pytest.fixture
def temp_files(mock_coefficients_data, mock_fpca_results):
    """Create temporary files for coefficients and FPCA results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        coeffs_path = tmpdir / "coefficients.pkl"
        fpca_path = tmpdir / "fpca_results.pkl"
        output_path = tmpdir / "loo_results.pkl"
        
        with open(coeffs_path, 'wb') as f:
            pickle.dump(mock_coefficients_data, f)
        
        with open(fpca_path, 'wb') as f:
            pickle.dump(mock_fpca_results, f)
        
        yield coeffs_path, fpca_path, output_path

def test_loo_iterations_match_ensemble_size(temp_files, mock_coefficients_data):
    """
    Test that the number of LOO iterations equals the ensemble size (N).
    This is the core requirement of T028a.
    """
    coeffs_path, fpca_path, output_path = temp_files
    N = len(mock_coefficients_data)
    
    # Mock perform_fpca to avoid dependency on scikit-fda or complex math in unit test
    # We need to patch the perform_fpca function in the robustness module
    with patch('robustness.perform_fpca') as mock_fpca:
        # Mock return value for perform_fpca
        mock_fpca.return_value = {
            'eigenfunctions': np.random.randn(5, 100),
            'eigenvalues': np.array([0.5, 0.3, 0.1, 0.05, 0.05])
        }
        
        results = run_loo_jackknife(
            fpca_results_path=str(fpca_path),
            coefficients_path=str(coeffs_path),
            output_path=str(output_path),
            n_components=5
        )
        
        # Assert validation
        assert results['validation']['expected_iterations'] == N
        assert results['validation']['actual_iterations'] == N
        assert results['validation']['is_valid'] is True
        
        # Assert that we have results for each removed model
        assert len(results['results']) == N
        
        # Verify that each result corresponds to a unique model removal
        removed_models = [r['removed_model'] for r in results['results']]
        assert len(set(removed_models)) == N
        assert set(removed_models) == set(mock_coefficients_data.keys())

def test_procrustes_align_function():
    """Test Procrustes alignment logic."""
    # Create two matrices that are similar but rotated/scaled
    np.random.seed(42)
    A = np.random.randn(10, 20)
    # Create B as a rotated version of A
    angle = np.pi / 4
    R = np.array([[np.cos(angle), -np.sin(angle)], 
                  [np.sin(angle), np.cos(angle)]])
    B = np.dot(A.T, R).T + np.random.randn(10, 20) * 0.01  # Add small noise
    
    aligned_B, scale = procrustes_align(A, B)
    
    # The aligned B should be very similar to A
    correlation = np.corrcoef(A.flatten(), aligned_B.flatten())[0, 1]
    assert correlation > 0.99  # Should be highly correlated

def test_calculate_stability_metrics():
    """Test stability metrics calculation."""
    np.random.seed(42)
    full = np.random.randn(5, 100)
    loo = full + np.random.randn(5, 100) * 0.01  # Very similar
    
    metrics = calculate_stability_metrics(full, loo)
    
    assert 'correlations' in metrics
    assert 'mean_correlation' in metrics
    assert 'std_correlation' in metrics
    assert 'min_correlation' in metrics
    
    # Correlations should be close to 1.0
    assert metrics['mean_correlation'] > 0.95
    assert metrics['std_correlation'] < 0.1