"""
Unit tests for T050: Regression input verification.
"""
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.analysis.regression import verify_regression_inputs


class TestRegressionInputVerification:
    """Tests for verify_regression_inputs function."""

    def _create_temp_error_rates(self, data: list, filename: str = "error_rates.csv") -> Path:
        """Create a temporary error_rates.csv file."""
        df = pd.DataFrame(data)
        with tempfile.NamedTemporaryFile(mode='w', suffix=filename, delete=False) as f:
            df.to_csv(f, index=False)
        return Path(f.name)

    def _create_temp_features(self, data: list, filename: str = "features.json") -> Path:
        """Create a temporary filtered_features.json file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=filename, delete=False) as f:
            json.dump(data, f)
        return Path(f.name)

    def test_valid_inputs(self):
        """Test with valid, matching inputs."""
        error_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'error_rate': 0.05},
            {'dataset_id': '2', 'hurst': 0.8, 'error_rate': 0.10},
        ]
        feature_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'acf_lag1': 0.5},
            {'dataset_id': '2', 'hurst': 0.8, 'acf_lag1': 0.6},
        ]

        err_path = self._create_temp_error_rates(error_data)
        feat_path = self._create_temp_features(feature_data)

        try:
            is_valid, msg = verify_regression_inputs(str(err_path), str(feat_path))
            assert is_valid is True
            assert "PASSED" in msg
        finally:
            err_path.unlink()
            feat_path.unlink()

    def test_mismatched_dataset_ids(self):
        """Test when dataset_ids do not match."""
        error_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'error_rate': 0.05},
            {'dataset_id': '3', 'hurst': 0.8, 'error_rate': 0.10},
        ]
        feature_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'acf_lag1': 0.5},
            {'dataset_id': '2', 'hurst': 0.8, 'acf_lag1': 0.6},
        ]

        err_path = self._create_temp_error_rates(error_data)
        feat_path = self._create_temp_features(feature_data)

        try:
            is_valid, msg = verify_regression_inputs(str(err_path), str(feat_path))
            assert is_valid is False
            assert "mismatch" in msg.lower()
        finally:
            err_path.unlink()
            feat_path.unlink()

    def test_nan_in_hurst(self):
        """Test when hurst column has NaN."""
        error_data = [
            {'dataset_id': '1', 'hurst': np.nan, 'error_rate': 0.05},
            {'dataset_id': '2', 'hurst': 0.8, 'error_rate': 0.10},
        ]
        feature_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'acf_lag1': 0.5},
            {'dataset_id': '2', 'hurst': 0.8, 'acf_lag1': 0.6},
        ]

        err_path = self._create_temp_error_rates(error_data)
        feat_path = self._create_temp_features(feature_data)

        try:
            is_valid, msg = verify_regression_inputs(str(err_path), str(feat_path))
            assert is_valid is False
            assert "NaN/Inf" in msg
        finally:
            err_path.unlink()
            feat_path.unlink()

    def test_inf_in_error_rate(self):
        """Test when error_rate column has Inf."""
        error_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'error_rate': np.inf},
            {'dataset_id': '2', 'hurst': 0.8, 'error_rate': 0.10},
        ]
        feature_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'acf_lag1': 0.5},
            {'dataset_id': '2', 'hurst': 0.8, 'acf_lag1': 0.6},
        ]

        err_path = self._create_temp_error_rates(error_data)
        feat_path = self._create_temp_features(feature_data)

        try:
            is_valid, msg = verify_regression_inputs(str(err_path), str(feat_path))
            assert is_valid is False
            assert "NaN/Inf" in msg
        finally:
            err_path.unlink()
            feat_path.unlink()

    def test_missing_error_rates_file(self):
        """Test when error_rates file does not exist."""
        feature_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'acf_lag1': 0.5},
        ]
        feat_path = self._create_temp_features(feature_data)

        try:
            is_valid, msg = verify_regression_inputs("nonexistent.csv", str(feat_path))
            assert is_valid is False
            assert "not found" in msg.lower()
        finally:
            feat_path.unlink()

    def test_duplicate_dataset_ids(self):
        """Test when dataset_ids are duplicated in error_rates."""
        error_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'error_rate': 0.05},
            {'dataset_id': '1', 'hurst': 0.75, 'error_rate': 0.06},
        ]
        feature_data = [
            {'dataset_id': '1', 'hurst': 0.7, 'acf_lag1': 0.5},
        ]

        err_path = self._create_temp_error_rates(error_data)
        feat_path = self._create_temp_features(feature_data)

        try:
            is_valid, msg = verify_regression_inputs(str(err_path), str(feat_path))
            assert is_valid is False
            assert "Duplicate" in msg
        finally:
            err_path.unlink()
            feat_path.unlink()