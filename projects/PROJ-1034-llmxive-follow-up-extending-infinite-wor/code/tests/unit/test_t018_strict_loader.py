"""
Unit tests for T018: Strict dataset loader.

These tests verify that the loader raises DataUnavailableError
on fetch failure and does NOT implement synthetic fallback.
"""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.loader import (
    DataUnavailableError,
    load_real_dataset,
    load_from_local_path,
    load_simulation_dataset
)


class TestDataUnavailableError:
    """Test the DataUnavailableError exception class."""
    
    def test_error_instantiation(self):
        """Test that DataUnavailableError can be instantiated."""
        error = DataUnavailableError("Test message", source="test-source")
        assert "Test message" in str(error)
        assert error.source == "test-source"
        assert error.message == "Test message"
    
    def test_error_without_source(self):
        """Test that DataUnavailableError works without source."""
        error = DataUnavailableError("Test message")
        assert error.source is None


class TestLoadRealDataset:
    """Test the load_real_dataset function."""
    
    @patch('src.data.loader.HF_AVAILABLE', False)
    def test_datasets_not_installed(self):
        """Test that error is raised when datasets library is not available."""
        with pytest.raises(DataUnavailableError) as exc_info:
            load_real_dataset("test/dataset")
        
        assert "not installed" in str(exc_info.value)
        assert exc_info.value.source == "pip-install"
    
    @patch('src.data.loader.HF_AVAILABLE', True)
    @patch('src.data.loader.load_dataset')
    def test_successful_load(self, mock_load_dataset):
        """Test successful dataset loading."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset
        
        result = load_real_dataset("test/dataset")
        
        assert result == mock_dataset
        mock_load_dataset.assert_called_once()
    
    @patch('src.data.loader.HF_AVAILABLE', True)
    @patch('src.data.loader.load_dataset')
    def test_fetch_failure_raises_error(self, mock_load_dataset):
        """Test that fetch failure raises DataUnavailableError."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with pytest.raises(DataUnavailableError) as exc_info:
            load_real_dataset("test/dataset")
        
        assert "Failed to fetch" in str(exc_info.value)
        assert exc_info.value.source == "test/dataset"


class TestLoadFromLocalPath:
    """Test the load_from_local_path function."""
    
    def test_file_not_found(self):
        """Test that error is raised when file doesn't exist."""
        with pytest.raises(DataUnavailableError) as exc_info:
            load_from_local_path("/nonexistent/path/file.parquet")
        
        assert "not found" in str(exc_info.value)
    
    @patch('src.data.loader.pd')
    def test_unsupported_format(self, mock_pd):
        """Test that error is raised for unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(DataUnavailableError) as exc_info:
                load_from_local_path(temp_path, file_format="xyz")
            
            assert "Unsupported" in str(exc_info.value)
        finally:
            os.unlink(temp_path)


class TestLoadSimulationDataset:
    """Test the main load_simulation_dataset function."""
    
    @patch('src.data.loader.load_from_local_path')
    def test_local_path_success(self, mock_local):
        """Test successful local path loading."""
        mock_dataset = MagicMock()
        mock_local.return_value = mock_dataset
        
        result = load_simulation_dataset(local_path="/test/path.parquet")
        
        assert result == mock_dataset
        mock_local.assert_called_once_with("/test/path.parquet")
    
    @patch('src.data.loader.load_from_local_path')
    @patch('src.data.loader.load_real_dataset')
    def test_local_fallback_to_remote(self, mock_remote, mock_local):
        """Test fallback to remote when local fails."""
        mock_local.side_effect = DataUnavailableError("Local failed")
        mock_dataset = MagicMock()
        mock_remote.return_value = mock_dataset
        
        result = load_simulation_dataset(local_path="/test/path.parquet")
        
        assert result == mock_dataset
        mock_local.assert_called_once()
        mock_remote.assert_called_once()
    
    @patch('src.data.loader.load_real_dataset')
    def test_remote_failure_raises_error(self, mock_remote):
        """Test that remote failure raises DataUnavailableError."""
        mock_remote.side_effect = DataUnavailableError("Remote failed")
        
        with pytest.raises(DataUnavailableError) as exc_info:
            load_simulation_dataset()
        
        assert "Remote failed" in str(exc_info.value)
        # Verify error is re-raised, not caught here
        mock_remote.assert_called_once()
    
    @patch('src.data.loader.load_real_dataset')
    def test_no_synthetic_fallback(self, mock_remote):
        """
        CRITICAL TEST: Verify that NO synthetic fallback is implemented.
        
        This test ensures that when load_real_dataset fails, the error
        propagates up without any fallback logic in this function.
        """
        mock_remote.side_effect = DataUnavailableError("Remote failed")
        
        # The function should raise the error, not return synthetic data
        with pytest.raises(DataUnavailableError):
            result = load_simulation_dataset()
            # If we get here without exception, the test fails
            pytest.fail("DataUnavailableError should have been raised")


class TestIntegration:
    """Integration tests for the loader module."""
    
    def test_error_propagation_chain(self):
        """Test that errors propagate correctly through the chain."""
        with patch('src.data.loader.HF_AVAILABLE', True):
            with patch('src.data.loader.load_dataset') as mock_load:
                mock_load.side_effect = Exception("Network timeout")
                
                # Should raise DataUnavailableError
                with pytest.raises(DataUnavailableError) as exc_info:
                    load_real_dataset("test/dataset")
                
                # Verify it's the right type of error
                assert isinstance(exc_info.value, DataUnavailableError)
                assert "Network timeout" in str(exc_info.value)
    
    def test_no_synthetic_data_in_loader(self):
        """
        Verify that the loader module does NOT contain synthetic data generation.
        
        This is a code inspection test to ensure T018 compliance.
        """
        import inspect
        from src.data.loader import load_simulation_dataset
        
        source = inspect.getsource(load_simulation_dataset)
        
        # Check for common synthetic generation patterns that should NOT exist
        forbidden_patterns = [
            "generate_synthetic",
            "np.random",
            "mock_data",
            "fake_data",
            "synthetic_fallback"
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source.lower(), \
                f"Found forbidden pattern '{pattern}' in load_simulation_dataset. " \
                "T018 must NOT implement synthetic fallback."