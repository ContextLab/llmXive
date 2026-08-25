"""
Unit tests for the entropy validation module (T019).

Tests verify:
1. NaN detection works correctly.
2. Range validation (min/max) works correctly.
3. Report generation contains expected keys.
4. Edge cases (empty file, missing file) are handled.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_entropy import validate_entropy_csv, DEFAULT_MIN_ENTROPY, DEFAULT_MAX_ENTROPY


class TestValidateEntropy:
    """Tests for the validate_entropy_csv function."""

    @pytest.fixture
    def valid_csv_path(self, tmp_path):
        """Create a valid entropy CSV file."""
        csv_path = tmp_path / "valid_entropy.csv"
        data = {
            "subject_id": [f"sub_{i:03d}" for i in range(5)],
            "parcel_0": [0.5, 0.6, 0.7, 0.8, 0.9],
            "parcel_1": [1.0, 1.1, 1.2, 1.3, 1.4],
            "parcel_2": [0.2, 0.3, 0.4, 0.5, 0.6],
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.fixture
    def nan_csv_path(self, tmp_path):
        """Create a CSV with NaN values."""
        csv_path = tmp_path / "nan_entropy.csv"
        data = {
            "subject_id": [f"sub_{i:03d}" for i in range(5)],
            "parcel_0": [0.5, np.nan, 0.7, 0.8, 0.9],
            "parcel_1": [1.0, 1.1, np.nan, 1.3, 1.4],
            "parcel_2": [0.2, 0.3, 0.4, 0.5, 0.6],
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.fixture
    def out_of_range_csv_path(self, tmp_path):
        """Create a CSV with values out of biological range."""
        csv_path = tmp_path / "out_of_range_entropy.csv"
        data = {
            "subject_id": [f"sub_{i:03d}" for i in range(5)],
            "parcel_0": [-0.5, 0.6, 0.7, 0.8, 0.9],  # Negative value
            "parcel_1": [1.0, 1.1, 1.2, 1.3, 4.5],  # Value > 3.0
            "parcel_2": [0.2, 0.3, 0.4, 0.5, 0.6],
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    def test_valid_csv_no_nan_in_range(self, valid_csv_path):
        """Test that a valid CSV passes all checks."""
        is_valid, details = validate_entropy_csv(valid_csv_path)
        
        assert is_valid is True
        assert details["total_nans"] == 0
        assert details["min_entropy"] >= DEFAULT_MIN_ENTROPY
        assert details["max_entropy"] <= DEFAULT_MAX_ENTROPY
        assert len(details["errors"]) == 0
        assert details["n_subjects"] == 5
        assert details["n_features"] == 3

    def test_nan_detection(self, nan_csv_path):
        """Test that NaN values are correctly detected."""
        is_valid, details = validate_entropy_csv(nan_csv_path)
        
        assert is_valid is False
        assert details["total_nans"] == 2
        assert any("NaN" in err for err in details["errors"])

    def test_out_of_range_low(self, out_of_range_csv_path):
        """Test detection of values below minimum threshold."""
        is_valid, details = validate_entropy_csv(out_of_range_csv_path)
        
        assert is_valid is False
        assert details["n_below_min"] == 1
        assert any("below minimum" in err for err in details["errors"])

    def test_out_of_range_high(self, out_of_range_csv_path):
        """Test detection of values above maximum threshold."""
        is_valid, details = validate_entropy_csv(out_of_range_csv_path)
        
        assert is_valid is False
        assert details["n_above_max"] == 1
        assert any("above maximum" in err for err in details["errors"])

    def test_missing_file_raises(self, tmp_path):
        """Test that a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            validate_entropy_csv(str(tmp_path / "nonexistent.csv"))

    def test_empty_csv_raises(self, tmp_path):
        """Test that an empty CSV raises ValueError."""
        csv_path = tmp_path / "empty.csv"
        csv_path.touch()
        
        with pytest.raises(ValueError):
            validate_entropy_csv(str(csv_path))

    def test_report_structure(self, valid_csv_path):
        """Test that the report contains all expected keys."""
        is_valid, details = validate_entropy_csv(valid_csv_path)
        
        expected_keys = [
            "file_path", "shape", "n_subjects", "n_features",
            "total_nans", "nan_per_feature", "min_entropy",
            "max_entropy", "mean_entropy", "std_entropy",
            "is_valid", "errors"
        ]
        
        for key in expected_keys:
            assert key in details

    def test_custom_range(self, valid_csv_path):
        """Test validation with custom min/max thresholds."""
        # Set a very strict range that should fail
        is_valid, details = validate_entropy_csv(
            valid_csv_path, min_val=0.0, max_val=0.5
        )
        
        # Some values are > 0.5, so it should fail
        assert is_valid is False
        assert details["n_above_max"] > 0

    def test_statistics_accuracy(self, valid_csv_path):
        """Test that calculated statistics match expected values."""
        is_valid, details = validate_entropy_csv(valid_csv_path)
        
        # Manually calculate expected stats from the fixture data
        # parcel_0: [0.5, 0.6, 0.7, 0.8, 0.9] -> mean=0.7, min=0.5, max=0.9
        # parcel_1: [1.0, 1.1, 1.2, 1.3, 1.4] -> mean=1.2, min=1.0, max=1.4
        # parcel_2: [0.2, 0.3, 0.4, 0.5, 0.6] -> mean=0.4, min=0.2, max=0.6
        
        # Overall min should be 0.2
        assert abs(details["min_entropy"] - 0.2) < 1e-6
        
        # Overall max should be 1.4
        assert abs(details["max_entropy"] - 1.4) < 1e-6

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
