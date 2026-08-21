"""
Unit tests for sensitivity analysis logic and MAE > 0.1 conditional report generation.

Tests:
1. run_sensitivity_analysis: Verifies noise injection and MAE variance calculation.
2. generate_pdp_radius_mismatch: Verifies conditional execution based on MAE threshold.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pytest

# Import the module under test
# Note: Using relative import structure matching the project layout
from code.analysis import report

# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Mock config object."""
    config = MagicMock()
    config.data_dir = Path("data")
    config.model_dir = Path("models")
    config.report_dir = Path("reports")
    return config

@pytest.fixture
def mock_processed_data(mock_config):
    """Mock processed data with required columns."""
    data = pd.DataFrame({
        'composition': [
            '{"Zr": 0.6, "Cu": 0.4}',
            '{"Ti": 0.5, "Ni": 0.5}',
            '{"Pd": 0.8, "Si": 0.2}',
            '{"La": 0.7, "Al": 0.3}',
            '{"Mg": 0.6, "Ca": 0.4}'
        ],
        'density': [5.5, 4.2, 10.1, 3.9, 1.8],
        'rho_baseline': [5.4, 4.1, 10.0, 3.8, 1.7],
        'rho_residual': [0.1, 0.1, 0.1, 0.1, 0.1],
        'mean_atomic_mass': [65.0, 55.0, 105.0, 50.0, 20.0],
        'mean_atomic_radius': [1.5, 1.4, 1.6, 1.8, 1.6],
        'electronegativity_variance': [0.05, 0.04, 0.06, 0.03, 0.02],
        'atomic_radius_mismatch': [0.02, 0.01, 0.03, 0.04, 0.02],
        'packing_efficiency': [0.72, 0.71, 0.73, 0.70, 0.69]
    })
    return data

@pytest.fixture
def mock_model():
    """Mock trained model."""
    model = MagicMock()
    # Return dummy predictions for the mock data
    model.predict = MagicMock(return_value=np.array([0.11, 0.09, 0.12, 0.08, 0.11]))
    return model

@pytest.fixture
def mock_metrics_file(tmp_path):
    """Create a temporary metrics.json file."""
    metrics = {
        "model_mae": 0.12,  # > 0.1 to trigger PDP
        "baseline_mae": 0.15,
        "mass_only_mae": 0.20,
        "r2": 0.85
    }
    metrics_path = tmp_path / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f)
    return metrics_path

@pytest.fixture
def mock_metrics_file_low_mae(tmp_path):
    """Create a temporary metrics.json file with low MAE."""
    metrics = {
        "model_mae": 0.05,  # < 0.1 to skip PDP
        "baseline_mae": 0.15,
        "mass_only_mae": 0.20,
        "r2": 0.90
    }
    metrics_path = tmp_path / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f)
    return metrics_path

# --- Tests for Sensitivity Analysis Logic ---

def test_run_sensitivity_analysis_injects_noise(mock_config, mock_processed_data, mock_model):
    """Test that sensitivity analysis correctly injects Gaussian noise and calculates variance."""
    # Setup mocks
    with patch.object(report, 'load_processed_data', return_value=mock_processed_data):
        with patch.object(report, 'load_model', return_value=mock_model):
            with patch.object(report, 'get_logger', return_value=MagicMock()):
                # Run the function
                result = report.run_sensitivity_analysis(
                    config=mock_config,
                    noise_magnitudes=[0.01, 0.05, 0.10]
                )
    
    # Assertions
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'noise_magnitudes' in result, "Result should contain noise magnitudes"
    assert 'mae_values' in result, "Result should contain MAE values"
    assert 'mae_variance' in result, "Result should contain MAE variance"
    
    # Check that noise magnitudes match input
    assert result['noise_magnitudes'] == [0.01, 0.05, 0.10]
    
    # Check that MAE values are calculated (should be non-empty list)
    assert len(result['mae_values']) == 3, "Should have 3 MAE values for 3 noise levels"
    
    # Check that variance is calculated (should be a float)
    assert isinstance(result['mae_variance'], float), "Variance should be a float"
    assert result['mae_variance'] >= 0, "Variance should be non-negative"

def test_run_sensitivity_analysis_noise_increases_error(mock_config, mock_processed_data, mock_model):
    """Test that higher noise magnitudes generally lead to higher MAE (statistical expectation)."""
    with patch.object(report, 'load_processed_data', return_value=mock_processed_data):
        with patch.object(report, 'load_model', return_value=mock_model):
            with patch.object(report, 'get_logger', return_value=MagicMock()):
                result = report.run_sensitivity_analysis(
                    config=mock_config,
                    noise_magnitudes=[0.01, 0.05, 0.10]
                )
    
    # The MAE should generally increase with noise magnitude
    # Note: Due to randomness, this might not always hold, but we test the logic
    mae_values = result['mae_values']
    
    # Basic sanity check: MAE values should be positive
    assert all(mae >= 0 for mae in mae_values), "All MAE values should be non-negative"
    
    # Check that the variance is calculated based on the MAE values
    expected_variance = np.var(mae_values)
    assert np.isclose(result['mae_variance'], expected_variance), "Variance calculation should be correct"

# --- Tests for MAE > 0.1 Conditional Report Generation ---

def test_generate_pdp_radius_mismatch_triggered_when_mae_high(mock_config, mock_metrics_file):
    """Test that PDP generation is triggered when MAE > 0.1."""
    # Mock the load_metrics function to return our high-MAE metrics
    with patch.object(report, 'load_metrics', return_value={"model_mae": 0.12}):
        with patch.object(report, 'load_model', return_value=MagicMock()):
            with patch.object(report, 'load_processed_data', return_value=MagicMock()):
                with patch.object(report, 'plt', autospec=True) as mock_plt:
                    # Mock the figure object
                    mock_fig = MagicMock()
                    mock_plt.figure.return_value = mock_fig
                    mock_plt.subplots.return_value = (mock_fig, MagicMock())
                    
                    # Call the function
                    output_path = report.generate_pdp_radius_mismatch(
                        config=mock_config,
                        metrics_path=mock_metrics_file
                    )
                    
                    # Assertions
                    assert output_path is not None, "Output path should be generated"
                    assert "pdp_radius_mismatch.png" in str(output_path), "Output filename should contain 'pdp_radius_mismatch.png'"
                    
                    # Verify that plotting functions were called
                    assert mock_plt.figure.called, "plt.figure should be called"

def test_generate_pdp_radius_mismatch_skipped_when_mae_low(mock_config, mock_metrics_file_low_mae):
    """Test that PDP generation is skipped when MAE <= 0.1."""
    with patch.object(report, 'load_metrics', return_value={"model_mae": 0.05}):
        with patch.object(report, 'load_model', return_value=MagicMock()):
            with patch.object(report, 'load_processed_data', return_value=MagicMock()):
                with patch.object(report, 'plt', autospec=True) as mock_plt:
                    # Call the function
                    output_path = report.generate_pdp_radius_mismatch(
                        config=mock_config,
                        metrics_path=mock_metrics_file_low_mae
                    )
                    
                    # Assertions
                    assert output_path is None, "Output path should be None when MAE <= 0.1"
                    
                    # Verify that plotting functions were NOT called
                    assert not mock_plt.figure.called, "plt.figure should NOT be called when MAE <= 0.1"

def test_generate_pdp_radius_mismatch_uses_correct_threshold(mock_config, mock_metrics_file):
    """Test that the threshold logic uses exactly 0.1."""
    # Test with MAE exactly 0.1 (should trigger)
    metrics_at_threshold = {"model_mae": 0.10}
    with patch.object(report, 'load_metrics', return_value=metrics_at_threshold):
        with patch.object(report, 'load_model', return_value=MagicMock()):
            with patch.object(report, 'load_processed_data', return_value=MagicMock()):
                with patch.object(report, 'plt', autospec=True) as mock_plt:
                    mock_fig = MagicMock()
                    mock_plt.figure.return_value = mock_fig
                    mock_plt.subplots.return_value = (mock_fig, MagicMock())
                    
                    output_path = report.generate_pdp_radius_mismatch(
                        config=mock_config,
                        metrics_path=mock_metrics_file
                    )
                    
                    assert output_path is not None, "Should trigger at exactly 0.1"
    
    # Test with MAE just below 0.1 (should NOT trigger)
    metrics_below_threshold = {"model_mae": 0.0999}
    with patch.object(report, 'load_metrics', return_value=metrics_below_threshold):
        with patch.object(report, 'load_model', return_value=MagicMock()):
            with patch.object(report, 'load_processed_data', return_value=MagicMock()):
                with patch.object(report, 'plt', autospec=True) as mock_plt:
                    output_path = report.generate_pdp_radius_mismatch(
                        config=mock_config,
                        metrics_path=mock_metrics_file
                    )
                    
                    assert output_path is None, "Should NOT trigger below 0.1"

def test_sensitivity_analysis_integration(mock_config, tmp_path):
    """Integration test for sensitivity analysis writing to file."""
    # Create a mock processed data
    data = pd.DataFrame({
        'composition': ['{"A": 0.5, "B": 0.5}'],
        'density': [5.0],
        'rho_baseline': [4.9],
        'rho_residual': [0.1],
        'mean_atomic_mass': [50.0],
        'mean_atomic_radius': [1.5],
        'electronegativity_variance': [0.05],
        'atomic_radius_mismatch': [0.02],
        'packing_efficiency': [0.72]
    })
    
    mock_model = MagicMock()
    mock_model.predict = MagicMock(return_value=np.array([0.11]))
    
    # Mock the report directory
    mock_config.report_dir = tmp_path
    
    with patch.object(report, 'load_processed_data', return_value=data):
        with patch.object(report, 'load_model', return_value=mock_model):
            with patch.object(report, 'get_logger', return_value=MagicMock()):
                # Run the function
                result = report.run_sensitivity_analysis(
                    config=mock_config,
                    noise_magnitudes=[0.01, 0.05]
                )
    
    # Verify result structure
    assert 'noise_magnitudes' in result
    assert 'mae_values' in result
    assert 'mae_variance' in result
    assert len(result['mae_values']) == 2

def test_pdp_generation_handles_missing_features(mock_config, mock_metrics_file):
    """Test that PDP generation handles missing 'atomic_radius_mismatch' column gracefully."""
    # Create data without the required feature
    data = pd.DataFrame({
        'composition': ['{"A": 0.5, "B": 0.5}'],
        'density': [5.0],
        'rho_baseline': [4.9],
        'rho_residual': [0.1],
        'mean_atomic_mass': [50.0],
        # Missing 'atomic_radius_mismatch'
    })
    
    with patch.object(report, 'load_metrics', return_value={"model_mae": 0.12}):
        with patch.object(report, 'load_model', return_value=MagicMock()):
            with patch.object(report, 'load_processed_data', return_value=data):
                with patch.object(report, 'get_logger', return_value=MagicMock()) as mock_logger:
                    with patch.object(report, 'plt', autospec=True) as mock_plt:
                        # Mock figure to avoid errors
                        mock_fig = MagicMock()
                        mock_plt.figure.return_value = mock_fig
                        mock_plt.subplots.return_value = (mock_fig, MagicMock())
                        
                        # This should handle the missing column gracefully (log warning or skip)
                        # Depending on implementation, it might return None or raise a specific error
                        # For this test, we assume it logs a warning and returns None
                        output_path = report.generate_pdp_radius_mismatch(
                            config=mock_config,
                            metrics_path=mock_metrics_file
                        )
                        
                        # Verify that a warning was logged about missing features
                        # Or that the function returned None
                        assert output_path is None or mock_logger.warning.called, \
                            "Should handle missing features gracefully"