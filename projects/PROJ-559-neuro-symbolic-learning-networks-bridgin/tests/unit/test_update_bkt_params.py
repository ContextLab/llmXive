"""
Unit tests for update_bkt_params.py

Tests the parameter update logic based on calibration metrics.
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulate.update_bkt_params import (
    calculate_adjustment,
    validate_params,
    load_metrics,
    load_params,
    save_params,
    run_update
)


class TestCalculateAdjustment:
    """Tests for the calculate_adjustment function."""

    def test_positive_rmse_diff_increases_p_l0(self):
        """When RMSE diff is positive, P_L0 should increase."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        adjusted = calculate_adjustment(0.05, params, learning_rate=0.05)
        assert adjusted['P_L0'] > params['P_L0']

    def test_positive_rmse_diff_decreases_p_s(self):
        """When RMSE diff is positive, P_S should decrease."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        adjusted = calculate_adjustment(0.05, params, learning_rate=0.05)
        assert adjusted['P_S'] < params['P_S']

    def test_negative_rmse_diff_decreases_p_l0(self):
        """When RMSE diff is negative, P_L0 should decrease."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        adjusted = calculate_adjustment(-0.05, params, learning_rate=0.05)
        assert adjusted['P_L0'] < params['P_L0']

    def test_negative_rmse_diff_increases_p_s(self):
        """When RMSE diff is negative, P_S should increase."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        adjusted = calculate_adjustment(-0.05, params, learning_rate=0.05)
        assert adjusted['P_S'] > params['P_S']

    def test_zero_rmse_diff_no_change(self):
        """When RMSE diff is zero, parameters should remain unchanged."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        adjusted = calculate_adjustment(0.0, params, learning_rate=0.05)
        assert adjusted['P_L0'] == params['P_L0']
        assert adjusted['P_S'] == params['P_S']

    def test_parameters_clamped_to_valid_range(self):
        """Parameters should be clamped to [0, 1]."""
        params = {'P_G': 0.1, 'P_L0': 0.99, 'P_S': 0.01, 'P_T': 0.1}
        # Large positive diff should try to increase P_L0 beyond 1.0
        adjusted = calculate_adjustment(0.5, params, learning_rate=0.5)
        assert adjusted['P_L0'] <= 1.0
        assert adjusted['P_S'] >= 0.0

    def test_p_g_and_p_t_unchanged(self):
        """P_G and P_T should remain unchanged in this adjustment logic."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        adjusted = calculate_adjustment(0.05, params, learning_rate=0.05)
        assert adjusted['P_G'] == params['P_G']
        assert adjusted['P_T'] == params['P_T']


class TestValidateParams:
    """Tests for the validate_params function."""

    def test_valid_parameters(self):
        """Valid parameters should return True."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        assert validate_params(params) is True

    def test_missing_parameter(self):
        """Missing required parameter should return False."""
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2}
        assert validate_params(params) is False

    def test_parameter_out_of_range(self):
        """Parameter out of [0, 1] range should return False."""
        params = {'P_G': 0.1, 'P_L0': 1.5, 'P_S': 0.2, 'P_T': 0.1}
        assert validate_params(params) is False

    def test_negative_parameter(self):
        """Negative parameter should return False."""
        params = {'P_G': -0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        assert validate_params(params) is False


class TestRunUpdate:
    """Tests for the run_update function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_successful_update(self, temp_dir):
        """Test successful parameter update."""
        metrics_path = os.path.join(temp_dir, 'metrics.json')
        params_path = os.path.join(temp_dir, 'params.yaml')
        report_path = os.path.join(temp_dir, 'report.json')

        # Create test metrics
        metrics = {'rmse_difference': 0.05, 'absolute_rmse': 0.1}
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)

        # Create test params
        params = {'P_G': 0.1, 'P_L0': 0.5, 'P_S': 0.2, 'P_T': 0.1}
        with open(params_path, 'w') as f:
            import yaml
            yaml.dump(params, f)

        # Run update
        result = run_update(
            metrics_path=metrics_path,
            params_path=params_path,
            report_path=report_path,
            learning_rate=0.05
        )

        assert result['status'] == 'success'
        assert result['updated_params']['P_L0'] > params['P_L0']
        assert os.path.exists(report_path)

    def test_missing_metrics_file(self, temp_dir):
        """Test handling of missing metrics file."""
        result = run_update(
            metrics_path=os.path.join(temp_dir, 'nonexistent.json'),
            params_path=os.path.join(temp_dir, 'params.yaml')
        )
        assert result['status'] == 'failed'
        assert 'not found' in result['error'].lower()

    def test_missing_params_file(self, temp_dir):
        """Test handling of missing params file."""
        metrics_path = os.path.join(temp_dir, 'metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump({'rmse_difference': 0.05}, f)

        result = run_update(
            metrics_path=metrics_path,
            params_path=os.path.join(temp_dir, 'nonexistent.yaml')
        )
        assert result['status'] == 'failed'
        assert 'not found' in result['error'].lower()