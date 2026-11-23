"""
Unit tests for src/data/validation.py
"""
import pytest
import pandas as pd
import numpy as np

from src.data.validation import (
    validate_intensity_scores,
    validate_message_ids,
    run_full_validation
)
from src.data.loaders import DataUnavailableError


class TestValidateIntensityScores:
    """Tests for validate_intensity_scores function."""

    def test_missing_column_raises_data_unavailable(self):
        """Test that missing 'human_intensity_score' raises DataUnavailableError."""
        df = pd.DataFrame({"message_id": [1, 2], "text": ["hello", "world"]})
        
        with pytest.raises(DataUnavailableError) as exc_info:
            validate_intensity_scores(df)
        
        assert "human_intensity_score" in str(exc_info.value)

    def test_non_numeric_column_raises_value_error(self):
        """Test that non-numeric intensity scores raise ValueError."""
        df = pd.DataFrame({
            "message_id": [1, 2],
            "human_intensity_score": ["low", "high"]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_intensity_scores(df)
        
        assert "not numeric" in str(exc_info.value)

    def test_missing_values_raises_value_error(self):
        """Test that NaN values in intensity scores raise ValueError."""
        df = pd.DataFrame({
            "message_id": [1, 2, 3],
            "human_intensity_score": [1.0, np.nan, 5.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_intensity_scores(df)
        
        assert "missing" in str(exc_info.value).lower() or "nan" in str(exc_info.value).lower()

    def test_valid_data_returns_true(self):
        """Test that valid data passes validation."""
        df = pd.DataFrame({
            "message_id": [1, 2, 3],
            "human_intensity_score": [1.0, 3.0, 5.0]
        })
        
        is_valid, error_msg = validate_intensity_scores(df)
        
        assert is_valid is True
        assert error_msg is None

    def test_valid_data_0_to_5_range(self):
        """Test that 0-5 scale is accepted."""
        df = pd.DataFrame({
            "message_id": [1, 2],
            "human_intensity_score": [0.0, 5.0]
        })
        
        is_valid, error_msg = validate_intensity_scores(df)
        assert is_valid is True

    def test_invalid_range_raises_error(self):
        """Test that implausible ranges raise ValueError."""
        df = pd.DataFrame({
            "message_id": [1, 2],
            "human_intensity_score": [0.0, 1000.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_intensity_scores(df)
        
        assert "implausible" in str(exc_info.value)

    def test_empty_dataframe_returns_false(self):
        """Test that empty dataframe returns False with error message."""
        df = pd.DataFrame(columns=["message_id", "human_intensity_score"])
        
        is_valid, error_msg = validate_intensity_scores(df)
        
        assert is_valid is False
        assert "empty" in error_msg.lower()


class TestValidateMessageIds:
    """Tests for validate_message_ids function."""

    def test_missing_message_id_raises_data_unavailable(self):
        """Test that missing 'message_id' raises DataUnavailableError."""
        df = pd.DataFrame({"text": ["hello"]})
        
        with pytest.raises(DataUnavailableError) as exc_info:
            validate_message_ids(df)
        
        assert "message_id" in str(exc_info.value)

    def test_missing_values_in_id_raises_value_error(self):
        """Test that NaN in message_id raises ValueError."""
        df = pd.DataFrame({
            "message_id": [1, np.nan, 3],
            "human_intensity_score": [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_message_ids(df)
        
        assert "missing" in str(exc_info.value).lower()

    def test_duplicate_ids_raises_value_error(self):
        """Test that duplicate message_ids raise ValueError."""
        df = pd.DataFrame({
            "message_id": [1, 1, 2],
            "human_intensity_score": [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_message_ids(df)
        
        assert "duplicate" in str(exc_info.value).lower()

    def test_valid_ids_returns_true(self):
        """Test that unique, non-null message_ids pass validation."""
        df = pd.DataFrame({
            "message_id": [1, 2, 3],
            "human_intensity_score": [1.0, 2.0, 3.0]
        })
        
        is_valid, error_msg = validate_message_ids(df)
        
        assert is_valid is True
        assert error_msg is None


class TestRunFullValidation:
    """Tests for run_full_validation function."""

    def test_valid_dataset_passes(self):
        """Test that a fully valid dataset passes all checks."""
        df = pd.DataFrame({
            "message_id": [1, 2, 3],
            "human_intensity_score": [1.0, 3.0, 5.0],
            "text": ["a", "b", "c"]
        })
        
        result = run_full_validation(df)
        assert result is True

    def test_missing_intensity_score_raises(self):
        """Test that missing intensity score raises DataUnavailableError."""
        df = pd.DataFrame({
            "message_id": [1, 2],
            "text": ["a", "b"]
        })
        
        with pytest.raises(DataUnavailableError):
            run_full_validation(df)

    def test_duplicate_ids_raises(self):
        """Test that duplicate IDs raise ValueError."""
        df = pd.DataFrame({
            "message_id": [1, 1],
            "human_intensity_score": [1.0, 2.0]
        })
        
        with pytest.raises(ValueError):
            run_full_validation(df)