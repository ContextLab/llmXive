"""
Unit tests for DataUnavailableError raising in src/data/loaders.py.

Verifies that the loader raises an error immediately when
human_intensity_score is missing from the dataset.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.data.loaders import DataUnavailableError, load_raw_text_corpus

def test_load_raises_on_missing_intensity():
    """
    Test that load_raw_text_corpus raises DataUnavailableError
    when human_intensity_score is missing.
    
    This test mocks the dataset loading to return a DataFrame without
    the required 'human_intensity_score' column, ensuring the loader
    raises the specific error and halts execution.
    """
    # Create a mock DataFrame that mimics the dataset structure but lacks the required column
    mock_data = pd.DataFrame({
        "message_id": ["msg_001", "msg_002"],
        "text": ["Hello world", "Test message"],
        # Note: 'human_intensity_score' is intentionally missing
    })

    # Mock the datasets.load_dataset to return our mock data
    with patch("src.data.loaders.load_dataset") as mock_load_dataset:
        mock_load_dataset.return_value = mock_data

        # The loader should raise DataUnavailableError because 'human_intensity_score' is missing
        with pytest.raises(DataUnavailableError) as excinfo:
            load_raw_text_corpus("cmu/text_messages_v1")

        # Verify the error message is informative
        assert "human_intensity_score" in str(excinfo.value)
        assert "missing" in str(excinfo.value).lower()

def test_data_unavailable_error_message():
    """Test that the error message is informative and specific."""
    error_msg = "Dataset 'test_dataset' is missing required column: human_intensity_score"
    with pytest.raises(DataUnavailableError, match="human_intensity_score"):
        raise DataUnavailableError(error_msg)

def test_load_succeeds_when_intensity_present():
    """
    Test that load_raw_text_corpus succeeds when human_intensity_score is present.
    
    This ensures the error logic is strictly conditional and doesn't block valid data.
    """
    # Create a mock DataFrame with the required column
    mock_data = pd.DataFrame({
        "message_id": ["msg_001", "msg_002"],
        "text": ["Hello world", "Test message"],
        "human_intensity_score": [3.5, 4.2],
    })

    with patch("src.data.loaders.load_dataset") as mock_load_dataset:
        mock_load_dataset.return_value = mock_data

        # This should NOT raise an error
        try:
            result = load_raw_text_corpus("cmu/text_messages_v1")
            # If we get here without exception, the test passes
            assert isinstance(result, pd.DataFrame)
            assert "human_intensity_score" in result.columns
        except DataUnavailableError:
            pytest.fail("load_raw_text_corpus raised DataUnavailableError even though human_intensity_score was present")