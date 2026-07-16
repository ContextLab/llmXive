"""
Unit tests for data_loading module.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.data_loading import (
    load_dundee_eye_tracking,
    load_boston_eye_tracking,
    fetch_eye_tracking_data,
    validate_eye_tracking_schema
)


class TestValidateEyeTrackingSchema:
    """Tests for schema validation."""

    def test_valid_schema(self):
        """Test that a DataFrame with required columns passes validation."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'trial_id': [101, 102],
            'timestamp': [0.0, 10.0],
            'x': [100.0, 200.0],
            'y': [150.0, 250.0]
        })
        assert validate_eye_tracking_schema(df) is True

    def test_missing_columns(self):
        """Test that a DataFrame with missing columns fails validation."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'trial_id': [101, 102],
            'timestamp': [0.0, 10.0]
            # Missing 'x' and 'y'
        })
        assert validate_eye_tracking_schema(df) is False

    def test_extra_columns(self):
        """Test that a DataFrame with extra columns still passes validation."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'trial_id': [101, 102],
            'timestamp': [0.0, 10.0],
            'x': [100.0, 200.0],
            'y': [150.0, 250.0],
            'extra_column': ['a', 'b']
        })
        assert validate_eye_tracking_schema(df) is True


class TestFetchEyeTrackingData:
    """Tests for the fetch_eye_tracking_data function."""

    @patch('utils.data_loading.load_dundee_eye_tracking')
    def test_fetch_dundee(self, mock_load):
        """Test fetching Dundee data."""
        mock_df = pd.DataFrame({'participant_id': [1]})
        mock_load.return_value = mock_df

        result = fetch_eye_tracking_data(source="dundee")

        mock_load.assert_called_once_with(split="train", streaming=False, revision=None)
        assert result.equals(mock_df)

    @patch('utils.data_loading.load_boston_eye_tracking')
    def test_fetch_boston(self, mock_load):
        """Test fetching Boston data."""
        mock_df = pd.DataFrame({'participant_id': [1]})
        mock_load.return_value = mock_df

        result = fetch_eye_tracking_data(source="boston")

        mock_load.assert_called_once_with(split="train", streaming=False, revision=None)
        assert result.equals(mock_df)

    def test_fetch_unknown_source(self):
        """Test that fetching from an unknown source raises ValueError."""
        with pytest.raises(ValueError, match="Unknown eye-tracking source"):
            fetch_eye_tracking_data(source="unknown")

    @patch('utils.data_loading.load_dundee_eye_tracking')
    def test_fetch_with_custom_params(self, mock_load):
        """Test fetching with custom parameters."""
        mock_df = pd.DataFrame({'participant_id': [1]})
        mock_load.return_value = mock_df

        result = fetch_eye_tracking_data(
            source="dundee",
            split="test",
            streaming=True,
            revision="v1.0.0"
        )

        mock_load.assert_called_once_with(split="test", streaming=True, revision="v1.0.0")
        assert result.equals(mock_df)


class TestLoadDundeeEyeTracking:
    """Tests for load_dundee_eye_tracking."""

    @patch('utils.data_loading.load_dataset')
    def test_load_dundee_success(self, mock_load_dataset):
        """Test successful loading of Dundee dataset."""
        # Mock the dataset object
        mock_ds = MagicMock()
        mock_ds.to_pandas.return_value = pd.DataFrame({'participant_id': [1]})
        mock_load_dataset.return_value = mock_ds

        result = load_dundee_eye_tracking()

        mock_load_dataset.assert_called_once_with(
            "nab/dundee_eye_tracking_corpus",
            split="train",
            streaming=False,
            revision=None
        )
        assert isinstance(result, pd.DataFrame)

    @patch('utils.data_loading.load_dataset')
    def test_load_dundee_failure(self, mock_load_dataset):
        """Test that failure to load raises RuntimeError."""
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError, match="Failed to load verified eye-tracking data"):
            load_dundee_eye_tracking()


class TestLoadBostonEyeTracking:
    """Tests for load_boston_eye_tracking."""

    @patch('utils.data_loading.load_dataset')
    def test_load_boston_success(self, mock_load_dataset):
        """Test successful loading of Boston dataset."""
        mock_ds = MagicMock()
        mock_ds.to_pandas.return_value = pd.DataFrame({'participant_id': [1]})
        mock_load_dataset.return_value = mock_ds

        result = load_boston_eye_tracking()

        mock_load_dataset.assert_called_once_with(
            "nab/boston_university_eye_tracking",
            split="train",
            streaming=False,
            revision=None
        )
        assert isinstance(result, pd.DataFrame)

    @patch('utils.data_loading.load_dataset')
    def test_load_boston_failure(self, mock_load_dataset):
        """Test that failure to load raises RuntimeError."""
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError, match="Failed to load verified eye-tracking data"):
            load_boston_eye_tracking()