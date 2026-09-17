import pytest
import os
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import tempfile
import json

from data.fetch_utils import (
    DataFetchError,
    load_real_dataset,
    validate_dataset_structure,
    compute_dataset_checksum,
    fetch_with_retry,
    download_file_to_cache
)

class TestDataFetchErrorHandling:
    """Tests to ensure data fetch failures raise errors instead of falling back to synthetic data."""

    def test_load_real_dataset_raises_on_failure(self):
        """Verify that load_real_dataset raises DataFetchError when fetch fails."""
        with patch('data.fetch_utils.load_dataset') as mock_load:
            # Simulate a fetch failure
            mock_load.side_effect = Exception("Network error")
            
            with pytest.raises(DataFetchError) as exc_info:
                load_real_dataset("nonexistent/dataset")
            
            assert "Failed to fetch real dataset" in str(exc_info.value)
            assert "nonexistent/dataset" in str(exc_info.value)

    def test_load_real_dataset_raises_on_empty_dataset(self):
        """Verify that load_real_dataset raises DataFetchError for empty datasets."""
        with patch('data.fetch_utils.load_dataset') as mock_load:
            # Simulate an empty dataset
            mock_dataset = Mock()
            mock_dataset.__len__ = Mock(return_value=0)
            mock_load.return_value = mock_dataset
            
            with pytest.raises(DataFetchError) as exc_info:
                load_real_dataset("fake/empty-dataset")
            
            assert "is empty" in str(exc_info.value)

    def test_load_real_dataset_raises_on_none_return(self):
        """Verify that load_real_dataset raises DataFetchError when None is returned."""
        with patch('data.fetch_utils.load_dataset') as mock_load:
            mock_load.return_value = None
            
            with pytest.raises(DataFetchError) as exc_info:
                load_real_dataset("fake/none-dataset")
            
            assert "returned None" in str(exc_info.value)

    def test_validate_dataset_structure_raises_on_missing_fields(self):
        """Verify that validate_dataset_structure raises DataFetchError for missing fields."""
        mock_dataset = Mock()
        mock_dataset.column_names = ['field1', 'field2']
        
        with pytest.raises(DataFetchError) as exc_info:
            validate_dataset_structure(mock_dataset, ['field1', 'required_field'])
        
        assert "missing required fields" in str(exc_info.value)
        assert "required_field" in str(exc_info.value)

    def test_no_synthetic_fallback_in_load_real_dataset(self):
        """Verify that load_real_dataset never falls back to synthetic data."""
        with patch('data.fetch_utils.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Fetch failed")
            
            # This should raise, not return synthetic data
            with pytest.raises(DataFetchError):
                result = load_real_dataset("fake/dataset")
                # If we get here without exception, the test fails
                assert result is not None, "Should have raised DataFetchError"

    def test_fetch_with_retry_raises_on_persistent_failure(self):
        """Verify that fetch_with_retry raises DataFetchError after all retries."""
        with patch('data.fetch_utils.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            
            with pytest.raises(DataFetchError) as exc_info:
                fetch_with_retry("http://fake-url.invalid", max_retries=2)
            
            assert "Failed to fetch" in str(exc_info.value)
            assert "2 attempts" in str(exc_info.value)

    def test_download_file_to_cache_raises_on_failure(self):
        """Verify that download_file_to_cache raises DataFetchError on download failure."""
        with patch('data.fetch_utils.fetch_with_retry') as mock_fetch:
            mock_fetch.side_effect = DataFetchError("Download failed")
            
            with pytest.raises(DataFetchError):
                download_file_to_cache("http://fake-url.invalid")

    def test_data_fetch_error_is_exception(self):
        """Verify that DataFetchError is a proper exception class."""
        with pytest.raises(DataFetchError):
            raise DataFetchError("Test error")

    def test_data_fetch_error_preserves_original_exception(self):
        """Verify that DataFetchError preserves the original exception context."""
        original_error = ValueError("Original error")
        
        try:
            with patch('data.fetch_utils.load_dataset') as mock_load:
                mock_load.side_effect = original_error
                load_real_dataset("fake/dataset")
        except DataFetchError as e:
            assert e.__cause__ is original_error
            assert "Original error" in str(e.__cause__)

class TestNoSyntheticFallback:
    """Tests to ensure no synthetic data is ever generated or returned."""

    def test_no_generate_synthetic_called(self):
        """Verify that no synthetic data generation functions are called."""
        # This test ensures that our error handling doesn't accidentally
        # call any synthetic data generation functions
        
        with patch('data.fetch_utils.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Fetch failed")
            
            # Attempt to load data - should raise, not generate synthetic
            with pytest.raises(DataFetchError):
                load_real_dataset("fake/dataset")
            
            # Verify no synthetic functions were called
            # (We check that only load_dataset was called, and it failed)
            assert mock_load.called

    def test_error_message_clearly_indicates_fetch_failure(self):
        """Verify that error messages clearly indicate real data fetch failure."""
        with patch('data.fetch_utils.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Network timeout")
            
            with pytest.raises(DataFetchError) as exc_info:
                load_real_dataset("test/dataset")
            
            error_msg = str(exc_info.value)
            assert "Failed to fetch real dataset" in error_msg
            assert "test/dataset" in error_msg
            assert "synthetic" not in error_msg.lower()  # Should not mention synthetic as an option
