"""
Unit tests for dataset validation logic.
Tests validation utility from T005 for missing behavioral measures.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.validation import (
    validate_eeg_channels,
    validate_behavioral_metrics,
    validate_dataframe_not_empty,
    exit_on_validation_failure,
)


class TestValidationUtils:
    """Test suite for validation utilities."""

    def test_validate_eeg_channels_present(self):
        """Test that validation passes when all required channels are present."""
        required_channels = {"F3", "F4", "Fz", "P3", "P4", "Pz"}
        available_channels = list(required_channels | {"Cz", "Oz"})
        result = validate_eeg_channels(available_channels)
        assert result is True

    def test_validate_eeg_channels_missing(self):
        """Test that validation fails when required channels are missing."""
        required_channels = {"F3", "F4", "Fz", "P3", "P4", "Pz"}
        available_channels = ["F3", "F4", "Cz"]  # Missing Fz, P3, P4, Pz
        result = validate_eeg_channels(available_channels)
        assert result is False

    def test_validate_behavioral_metrics_present(self):
        """Test validation passes when behavioral metrics are present."""
        metrics = {"k_score": [0.5, 0.6, 0.7], "d_prime": [1.2, 1.3, 1.4]}
        result = validate_behavioral_metrics(metrics)
        assert result is True

    def test_validate_behavioral_metrics_missing(self):
        """Test validation fails when behavioral metrics are missing."""
        metrics = {}  # Empty metrics
        result = validate_behavioral_metrics(metrics)
        assert result is False

    def test_validate_dataframe_not_empty(self):
        """Test that validation passes for non-empty dataframe."""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        result = validate_dataframe_not_empty(df)
        assert result is True

    def test_validate_dataframe_empty(self):
        """Test that validation fails for empty dataframe."""
        df = pd.DataFrame()
        result = validate_dataframe_not_empty(df)
        assert result is False

    def test_validate_dataframe_empty_columns(self):
        """Test that validation fails for dataframe with no columns."""
        df = pd.DataFrame(columns=["col1", "col2"])
        result = validate_dataframe_not_empty(df)
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
