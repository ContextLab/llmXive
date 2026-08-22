"""
Unit tests for regression stability checks in T065.

Tests multicollinearity detection, singular matrix handling,
and fallback behavior.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.analysis.regression import (
    check_regression_stability,
    run_regression,
    verify_regression_inputs,
    RegressionError,
    VIF_THRESHOLD
)

from src.utils.logging import setup_logger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def setup_test_files(temp_dir):
    """Create test input files."""
    # Create error rates CSV
    error_rates_path = temp_dir / 'error_rates.csv'
    error_data = {
        'dataset_id': ['syn_1', 'syn_2', 'syn_3', 'syn_4', 'syn_5'],
        'error_rate': [0.04, 0.06, 0.08, 0.12, 0.15]
    }
    pd.DataFrame(error_data).to_csv(error_rates_path, index=False)
    
    # Create Hurst metrics JSON
    hurst_path = temp_dir / 'hurst_metrics.json'
    hurst_data = [
        {'dataset_id': 'syn_1', 'hurst_exponent': 0.51},
        {'dataset_id': 'syn_2', 'hurst_exponent': 0.60},
        {'dataset_id': 'syn_3', 'hurst_exponent': 0.70},
        {'dataset_id': 'syn_4', 'hurst_exponent': 0.80},
        {'dataset_id': 'syn_5', 'hurst_exponent': 0.90}
    ]
    with open(hurst_path, 'w') as f:
        json.dump(hurst_data, f)
    
    # Create filtered features JSON
    filtered_path = temp_dir / 'filtered_features.json'
    filtered_data = {
        'features': ['hurst_exponent'],
        'excluded_features': ['Max_ACF_Lag', 'spectral_peak_ratio'],
        'model_type': 'univariate_ols'
    }
    with open(filtered_path, 'w') as f:
        json.dump(filtered_data, f)
    
    return {
        'error_rates': str(error_rates_path),
        'hurst_metrics': str(hurst_path),
        'filtered_features': str(filtered_path)
    }


class TestRegressionStability:
    """Tests for regression stability checks."""

    def test_stable_design_matrix(self):
        """Test that a stable design matrix passes checks."""
        X = np.array([[0.5], [0.6], [0.7], [0.8], [0.9]])
        y = np.array([0.04, 0.06, 0.08, 0.12, 0.15])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        assert is_stable is True
        assert diagnostics['is_singular'] is False
        assert len(diagnostics['warnings']) == 0
        assert 'condition_number' in diagnostics
        assert diagnostics['condition_number'] < 1e10

    def test_singular_matrix_detection(self):
        """Test detection of singular/near-singular matrices."""
        # Create nearly identical features (collinear)
        X = np.array([[1.0], [1.0000001], [1.0000002], [1.0000003], [1.0000004]])
        y = np.array([0.04, 0.06, 0.08, 0.12, 0.15])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        # Should detect singularity or high condition number
        assert diagnostics['condition_number'] > 1e8 or not is_stable

    def test_constant_feature_detection(self):
        """Test detection of constant features."""
        X = np.array([[1.0], [1.0], [1.0], [1.0], [1.0]])
        y = np.array([0.04, 0.06, 0.08, 0.12, 0.15])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        assert is_stable is False
        assert any('constant' in w.lower() for w in diagnostics['warnings'])

    def test_insufficient_samples(self):
        """Test handling of insufficient samples."""
        X = np.array([[0.5]])
        y = np.array([0.04])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        assert is_stable is False
        assert any('insufficient' in w.lower() for w in diagnostics['warnings'])

    def test_nan_detection(self):
        """Test detection of NaN values."""
        X = np.array([[0.5], [np.nan], [0.7], [0.8], [0.9]])
        y = np.array([0.04, 0.06, 0.08, 0.12, 0.15])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        assert is_stable is False
        assert any('nan' in w.lower() for w in diagnostics['warnings'])

    def test_inf_detection(self):
        """Test detection of Inf values."""
        X = np.array([[0.5], [np.inf], [0.7], [0.8], [0.9]])
        y = np.array([0.04, 0.06, 0.08, 0.12, 0.15])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        assert is_stable is False
        assert any('inf' in w.lower() for w in diagnostics['warnings'])

    def test_vif_calculation(self):
        """Test VIF calculation for multi-feature case."""
        # Create two correlated features
        X = np.column_stack([
            np.array([0.5, 0.6, 0.7, 0.8, 0.9]),
            np.array([0.51, 0.61, 0.71, 0.81, 0.91])  # Highly correlated
        ])
        y = np.array([0.04, 0.06, 0.08, 0.12, 0.15])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        # VIF should be calculated
        assert 'vif_values' in diagnostics
        assert len(diagnostics['vif_values']) > 0

    def test_high_vif_warning(self):
        """Test that high VIF triggers warnings."""
        # Create highly collinear features
        X = np.column_stack([
            np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
            np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # Identical
        ])
        y = np.array([0.04, 0.06, 0.08, 0.12, 0.15])
        
        is_stable, diagnostics = check_regression_stability(X, y)
        
        # Should detect high VIF or singularity
        assert not is_stable or any('vif' in w.lower() for w in diagnostics['warnings'])

    def test_run_regression_with_stable_data(self, setup_test_files, temp_dir):
        """Test full regression run with stable data."""
        output_path = str(temp_dir / 'regression_model.json')
        
        result = run_regression(
            setup_test_files['error_rates'],
            setup_test_files['hurst_metrics'],
            setup_test_files['filtered_features'],
            output_path
        )
        
        assert result['status'] == 'success'
        assert 'slope' in result
        assert 'intercept' in result
        assert 'p_value' in result
        assert 'r_squared' in result
        assert 'vif' in result
        assert 'n_eff' in result
        assert 'slope_per_01_unit' in result
        assert result['stability_check'] == 'passed'
        
        # Verify output file was created
        assert Path(output_path).exists()

    def test_run_regression_with_missing_files(self, temp_dir):
        """Test regression with missing input files."""
        output_path = str(temp_dir / 'regression_model.json')
        
        with pytest.raises(Exception):
            run_regression(
                'nonexistent.csv',
                'nonexistent.json',
                'nonexistent.json',
                output_path
            )

    def test_run_regression_with_mismatched_ids(self, temp_dir):
        """Test regression with mismatched dataset IDs."""
        # Create error rates with different IDs
        error_path = str(temp_dir / 'error_rates.csv')
        pd.DataFrame({
            'dataset_id': ['A', 'B'],
            'error_rate': [0.05, 0.10]
        }).to_csv(error_path, index=False)
        
        # Create Hurst metrics with different IDs
        hurst_path = str(temp_dir / 'hurst_metrics.json')
        with open(hurst_path, 'w') as f:
            json.dump([
                {'dataset_id': 'C', 'hurst_exponent': 0.5},
                {'dataset_id': 'D', 'hurst_exponent': 0.7}
            ], f)
        
        filtered_path = str(temp_dir / 'filtered_features.json')
        with open(filtered_path, 'w') as f:
            json.dump({'features': ['hurst_exponent']}, f)
        
        output_path = str(temp_dir / 'regression_model.json')
        
        with pytest.raises(RegressionError):
            run_regression(error_path, hurst_path, filtered_path, output_path)

    def test_slope_per_01_unit_calculation(self, setup_test_files, temp_dir):
        """Test that slope_per_01_unit is correctly calculated."""
        output_path = str(temp_dir / 'regression_model.json')
        
        result = run_regression(
            setup_test_files['error_rates'],
            setup_test_files['hurst_metrics'],
            setup_test_files['filtered_features'],
            output_path
        )
        
        # slope_per_01_unit should be slope * 0.1
        expected = result['slope'] * 0.1
        assert abs(result['slope_per_01_unit'] - expected) < 1e-10

    def test_verify_inputs_success(self, setup_test_files):
        """Test input verification with valid files."""
        is_valid, error_msg = verify_regression_inputs(
            setup_test_files['error_rates'],
            setup_test_files['filtered_features'],
            setup_test_files['hurst_metrics']
        )
        
        assert is_valid is True
        assert error_msg == 'OK'

    def test_verify_inputs_missing_file(self, temp_dir):
        """Test input verification with missing file."""
        is_valid, error_msg = verify_regression_inputs(
            str(temp_dir / 'missing.csv'),
            str(temp_dir / 'missing.json'),
            str(temp_dir / 'missing.json')
        )
        
        assert is_valid is False
        assert 'not found' in error_msg

    def test_verify_inputs_nan_values(self, temp_dir):
        """Test input verification with NaN values."""
        # Create error rates with NaN
        error_path = str(temp_dir / 'error_rates.csv')
        pd.DataFrame({
            'dataset_id': ['A', 'B'],
            'error_rate': [0.05, np.nan]
        }).to_csv(error_path, index=False)
        
        # Create Hurst metrics
        hurst_path = str(temp_dir / 'hurst_metrics.json')
        with open(hurst_path, 'w') as f:
            json.dump([
                {'dataset_id': 'A', 'hurst_exponent': 0.5},
                {'dataset_id': 'B', 'hurst_exponent': 0.7}
            ], f)
        
        filtered_path = str(temp_dir / 'filtered_features.json')
        with open(filtered_path, 'w') as f:
            json.dump({'features': ['hurst_exponent']}, f)
        
        is_valid, error_msg = verify_regression_inputs(
            error_path,
            filtered_path,
            hurst_path
        )
        
        assert is_valid is False
        assert 'NaN' in error_msg