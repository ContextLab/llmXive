"""
Unit tests for the integrity checker module (T067).
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.integrity_checker import (
    validate_json_schema,
    validate_csv_schema,
    check_file_exists,
    compute_file_checksum
)

class TestIntegrityChecker:
    """Tests for integrity checker functions."""

    def test_validate_json_schema_metrics_valid(self, tmp_path):
        """Test validation of valid metrics JSON."""
        metrics_data = [
            {
                "source": "test_source",
                "length": 100,
                "hurst": 0.75,
                "acf_vector": [1.0, 0.5, 0.3] * 7 + [0.1],  # 21 elements
                "spectral_peak_ratio": 2.5,
                "is_shuffled": False
            }
        ]
        file_path = tmp_path / "metrics.json"
        with open(file_path, 'w') as f:
            json.dump(metrics_data, f)
        
        is_valid, error = validate_json_schema(file_path, 'metrics')
        assert is_valid is True
        assert error is None

    def test_validate_json_schema_metrics_invalid_missing_keys(self, tmp_path):
        """Test validation of metrics JSON with missing keys."""
        metrics_data = [
            {
                "source": "test_source",
                "length": 100
                # Missing hurst, acf_vector, etc.
            }
        ]
        file_path = tmp_path / "metrics.json"
        with open(file_path, 'w') as f:
            json.dump(metrics_data, f)
        
        is_valid, error = validate_json_schema(file_path, 'metrics')
        assert is_valid is False
        assert "missing keys" in error.lower()

    def test_validate_json_schema_regression_model_valid(self, tmp_path):
        """Test validation of valid regression model JSON."""
        regression_data = {
            "slope": 0.15,
            "intercept": 0.02,
            "p_value": 0.001,
            "vif": 1.2,
            "n_eff": 500,
            "r_squared": 0.85,
            "slope_per_01_unit": 0.015
        }
        file_path = tmp_path / "regression_model.json"
        with open(file_path, 'w') as f:
            json.dump(regression_data, f)
        
        is_valid, error = validate_json_schema(file_path, 'regression_model')
        assert is_valid is True
        assert error is None

    def test_validate_json_schema_filtered_features_valid(self, tmp_path):
        """Test validation of valid filtered features JSON."""
        features_data = {
            "filtered_features": ["hurst", "length", "n_eff"],
            "excluded_features": ["max_acf_lag", "spectral_density"]
        }
        file_path = tmp_path / "filtered_features.json"
        with open(file_path, 'w') as f:
            json.dump(features_data, f)
        
        is_valid, error = validate_json_schema(file_path, 'filtered_features')
        assert is_valid is True
        assert error is None

    def test_validate_csv_schema_valid(self, tmp_path):
        """Test validation of valid CSV."""
        df = pd.DataFrame({
            "hurst": [0.5, 0.7, 0.9],
            "error_rate": [0.05, 0.15, 0.30],
            "n_eff": [100, 80, 60],
            "configuration": ["config1", "config2", "config3"]
        })
        file_path = tmp_path / "error_rates.csv"
        df.to_csv(file_path, index=False)
        
        is_valid, error = validate_csv_schema(file_path, 
                                              ["hurst", "error_rate", "n_eff", "configuration"])
        assert is_valid is True
        assert error is None

    def test_validate_csv_schema_missing_columns(self, tmp_path):
        """Test validation of CSV with missing columns."""
        df = pd.DataFrame({
            "hurst": [0.5, 0.7],
            "error_rate": [0.05, 0.15]
            # Missing n_eff, configuration
        })
        file_path = tmp_path / "error_rates.csv"
        df.to_csv(file_path, index=False)
        
        is_valid, error = validate_csv_schema(file_path, 
                                              ["hurst", "error_rate", "n_eff", "configuration"])
        assert is_valid is False
        assert "missing columns" in error.lower()

    def test_check_file_exists(self, tmp_path):
        """Test file existence check."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        exists, error = check_file_exists(file_path)
        assert exists is True
        assert error is None

    def test_check_file_exists_missing(self, tmp_path):
        """Test file existence check for missing file."""
        file_path = tmp_path / "missing.txt"
        
        exists, error = check_file_exists(file_path)
        assert exists is False
        assert "does not exist" in error.lower()

    def test_compute_file_checksum(self, tmp_path):
        """Test checksum computation."""
        file_path = tmp_path / "test.txt"
        content = "test content for checksum"
        file_path.write_text(content)
        
        checksum = compute_file_checksum(file_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

    def test_compute_file_checksum_empty(self, tmp_path):
        """Test checksum computation for empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")
        
        checksum = compute_file_checksum(file_path)
        assert len(checksum) == 64