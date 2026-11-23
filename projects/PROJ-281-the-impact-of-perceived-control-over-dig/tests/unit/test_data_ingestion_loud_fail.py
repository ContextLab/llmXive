import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.services.data_ingestion import download_and_validate_dataset, DataFetchError

@patch("code.services.data_ingestion.load_dataset")
def test_loud_fail_on_download_error(mock_load_dataset, tmp_path):
    """
    Test that download_and_validate_dataset raises DataFetchError 
    instead of returning None or using synthetic data when the real fetch fails.
    """
    # Mock the load_dataset to raise a generic exception (simulating network failure)
    mock_load_dataset.side_effect = Exception("Network timeout")

    # We need to patch the DATA_RAW_DIR to point to our temp directory
    with patch("code.services.data_ingestion.DATA_RAW_DIR", tmp_path):
        with patch("code.services.data_ingestion.CHECKSUM_FILE", tmp_path / "checksum.json"):
            with pytest.raises(DataFetchError) as exc_info:
                download_and_validate_dataset()

            assert "Real data fetch failed" in str(exc_info.value)

@patch("code.services.data_ingestion.load_dataset")
def test_loud_fail_on_empty_dataset(mock_load_dataset, tmp_path):
    """
    Test that download_and_validate_dataset raises DataFetchError 
    when the dataset returned is empty.
    """
    # Mock an empty dataset
    mock_dataset = MagicMock()
    mock_dataset.__len__ = MagicMock(return_value=0)
    mock_load_dataset.return_value = mock_dataset

    with patch("code.services.data_ingestion.DATA_RAW_DIR", tmp_path):
        with patch("code.services.data_ingestion.CHECKSUM_FILE", tmp_path / "checksum.json"):
            with pytest.raises(DataFetchError) as exc_info:
                download_and_validate_dataset()

            assert "Downloaded dataset is empty" in str(exc_info.value)

@patch("code.services.data_ingestion.load_dataset")
def test_no_synthetic_fallback(mock_load_dataset, tmp_path):
    """
    Ensure that NO synthetic data generation or fallback occurs.
    The function must strictly fail on real data fetch errors.
    """
    mock_load_dataset.side_effect = ConnectionError("Failed to connect")

    with patch("code.services.data_ingestion.DATA_RAW_DIR", tmp_path):
        with patch("code.services.data_ingestion.CHECKSUM_FILE", tmp_path / "checksum.json"):
            with pytest.raises(DataFetchError):
                download_and_validate_dataset()
            
            # Verify that no CSV file was created (proving no synthetic fallback)
            csv_path = tmp_path / "social_media.csv"
            assert not csv_path.exists(), "Synthetic data file was created, violating loud fail principle"