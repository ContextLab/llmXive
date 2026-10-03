"""
Tests for the stats module (T023a).
Tests linear and polynomial regression model fitting functions.
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import yaml
import json

# Import the functions to test
from src.stats import (
    fit_linear,
    fit_polynomial,
    calculate_vif,
    run_regression,
    run_cross_validation,
    check_data_availability,
    prepare_regression_data
)


@pytest.fixture
def sample_linear_data():
    """Generate sample linear data: y = 2x + 3 + noise"""
    np.random.seed(42)
    n = 100
    X = np.random.rand(n, 2) * 10
    y = 2 * X[:, 0] + 3 * X[:, 1] + 5 + np.random.normal(0, 0.5, n)
    return X, y


@pytest.fixture
def sample_polynomial_data():
    """Generate sample polynomial data: y = x^2 + 2x + 1 + noise"""
    np.random.seed(42)
    n = 100
    X = np.random.rand(n, 1) * 5
    y = (X[:, 0] ** 2) + 2 * X[:, 0] + 1 + np.random.normal(0, 0.5, n)
    return X, y


class TestFitLinear:
    def test_fit_linear_basic(self, sample_linear_data):
        X, y = sample_linear_data
        result = fit_linear(X, y)
        
        assert "model" in result
        assert "coefficients" in result
        assert "intercept" in result
        assert "r_squared" in result
        assert result["r_squared"] > 0.9  # Should be high for linear data
        
    def test_fit_linear_empty_input(self):
        X = np.array([]).reshape(0, 2)
        y = np.array([])
        with pytest.raises(ValueError):
            fit_linear(X, y)
        
    def test_fit_linear_coefficients_count(self, sample_linear_data):
        X, y = sample_linear_data
        result = fit_linear(X, y)
        
        assert len(result["coefficients"]) == X.shape[1]
        for key in result["coefficients"]:
            assert isinstance(result["coefficients"][key], float)


class TestFitPolynomial:
    def test_fit_polynomial_basic(self, sample_polynomial_data):
        X, y = sample_polynomial_data
        result = fit_polynomial(X, y, degree=2)
        
        assert "model" in result
        assert "poly_features" in result
        assert "coefficients" in result
        assert "intercept" in result
        assert "r_squared" in result
        assert result["r_squared"] > 0.95  # Should be very high for polynomial data
        
    def test_fit_polynomial_invalid_degree(self, sample_polynomial_data):
        X, y = sample_polynomial_data
        with pytest.raises(ValueError):
            fit_polynomial(X, y, degree=1)
        
    def test_fit_polynomial_empty_input(self):
        X = np.array([]).reshape(0, 1)
        y = np.array([])
        with pytest.raises(ValueError):
            fit_polynomial(X, y, degree=2)


class TestCalculateVif:
    def test_calculate_vif_basic(self, sample_linear_data):
        X, y = sample_linear_data
        feature_names = ["x1", "x2"]
        vif_values = calculate_vif(X, feature_names)
        
        assert len(vif_values) == 2
        assert "x1" in vif_values
        assert "x2" in vif_values
        # VIF should be finite for independent features
        assert np.isfinite(vif_values["x1"])
        assert np.isfinite(vif_values["x2"])
        
    def test_calculate_vif_no_names(self, sample_linear_data):
        X, y = sample_linear_data
        vif_values = calculate_vif(X)
        
        assert len(vif_values) == 2
        assert "feature_0" in vif_values
        assert "feature_1" in vif_values


class TestRunRegression:
    def test_run_regression_linear(self, sample_linear_data):
        X, y = sample_linear_data
        feature_names = ["x1", "x2"]
        result = run_regression(X, y, feature_names, model_type="linear")
        
        assert result["model_type"] == "linear"
        assert "coefficients" in result
        assert "p_values" in result
        assert "r_squared" in result
        assert result["r_squared"] > 0.9
        
    def test_run_regression_polynomial(self, sample_polynomial_data):
        X, y = sample_polynomial_data
        feature_names = ["x1"]
        result = run_regression(X, y, feature_names, model_type="polynomial", degree=2)
        
        assert result["model_type"] == "polynomial"
        assert "coefficients" in result
        assert "p_values" in result
        assert result["r_squared"] > 0.95


class TestRunCrossValidation:
    def test_run_cross_validation_loocv(self, sample_linear_data):
        X, y = sample_linear_data
        # Use a small dataset to trigger LOOCV
        X_small = X[:10]
        y_small = y[:10]
        
        result = run_cross_validation(X_small, y_small, model_type="linear")
        
        assert "mean_r2" in result
        assert "std_dev" in result
        assert result["cv_type"] == "LOOCV"
        assert result["mean_r2"] > 0
        
    def test_run_cross_validation_kfold(self, sample_linear_data):
        X, y = sample_linear_data
        # Use a larger dataset to trigger KFold
        X_large = X[:60]
        y_large = y[:60]
        
        result = run_cross_validation(X_large, y_large, model_type="linear", n_splits=5)
        
        assert "mean_r2" in result
        assert "std_dev" in result
        assert result["cv_type"] == "5-fold"
        assert result["mean_r2"] > 0


class TestDataAvailability:
    @patch('src.stats.load_config')
    @patch('src.stats.get_paths')
    def test_insufficient_data_blocks_regression(self, mock_get_paths, mock_load_config):
        """Test that regression is blocked when data is insufficient"""
        mock_config = {"seeds": {"random": 42}}
        mock_load_config.return_value = mock_config
        
        mock_paths = {
            "state": Path(tempfile.mkdtemp()) / "state"
        }
        mock_get_paths.return_value = mock_paths
        
        # Create state file with blocked flag
        state_file = mock_paths["state"] / "data_availability.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            yaml.dump({"regression_blocked": True, "raw_count": 5}, f)
        
        available, count = check_data_availability()
        assert available is False
        assert count == 5
        
    @patch('src.stats.load_config')
    @patch('src.stats.get_paths')
    def test_sufficient_data_proceeds(self, mock_get_paths, mock_load_config):
        """Test that regression proceeds when data is sufficient"""
        mock_config = {"seeds": {"random": 42}}
        mock_load_config.return_value = mock_config
        
        mock_paths = {
            "state": Path(tempfile.mkdtemp()) / "state"
        }
        mock_get_paths.return_value = mock_paths
        
        # Create state file with sufficient data
        state_file = mock_paths["state"] / "data_availability.yaml"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            yaml.dump({"regression_blocked": False, "raw_count": 15}, f)
        
        available, count = check_data_availability()
        assert available is True
        assert count == 15


class TestPrepareRegressionData:
    @patch('src.stats.Path')
    def test_prepare_regression_data_success(self, mock_path_class):
        """Test successful data preparation"""
        # Create mock dataframe
        df_data = {
            'network_id': ['net1', 'net2', 'net3'],
            'degree': [3.0, 4.0, 5.0],
            'clustering': [0.1, 0.2, 0.3],
            'path_length': [2.0, 2.5, 3.0],
            'threshold': [0.5, 0.6, 0.7]
        }
        df = pd.DataFrame(df_data)
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path
        
        with patch('pandas.read_csv', return_value=df):
            X, y, feature_names = prepare_regression_data(mock_path)
            
            assert X.shape == (3, 3)
            assert len(y) == 3
            assert feature_names == ['degree', 'clustering', 'path_length']
            
    def test_prepare_regression_data_missing_file(self):
        """Test error when file is missing"""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            prepare_regression_data(mock_path)
            
    def test_prepare_regression_data_missing_columns(self):
        """Test error when required columns are missing"""
        df_data = {
            'network_id': ['net1', 'net2'],
            'degree': [3.0, 4.0]
        }
        df = pd.DataFrame(df_data)
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        with patch('pandas.read_csv', return_value=df):
            with pytest.raises(ValueError):
                prepare_regression_data(mock_path)