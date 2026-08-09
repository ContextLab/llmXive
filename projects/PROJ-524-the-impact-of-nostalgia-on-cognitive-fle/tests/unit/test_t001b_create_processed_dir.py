"""
Unit tests for T001b: Create data directory: data/processed/
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import code.task_t001b_create_processed_dir as task_module
from code.config import get_config

class TestCreateProcessedDirectory:
    """Tests for the create_processed_directory function."""

    @patch('code.task_t001b_create_processed_dir.get_config')
    @patch('code.task_t001b_create_processed_dir.ensure_dirs')
    @patch('code.task_t001b_create_processed_dir.log_info')
    def test_creates_directory_if_missing(self, mock_log_info, mock_ensure_dirs, mock_get_config):
        """Test that the function creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock config to return a path inside our temp dir
            mock_get_config.return_value = {'paths': {'processed': str(Path(tmpdir) / 'data' / 'processed')}}
            
            # The directory should not exist initially
            target_path = Path(tmpdir) / 'data' / 'processed'
            assert not target_path.exists()
            
            # Call the function
            result = task_module.create_processed_directory()
            
            # Verify directory was created
            assert result.exists()
            assert result.is_dir()
            assert result == target_path
            
            # Verify logging occurred
            mock_log_info.assert_called()

    @patch('code.task_t001b_create_processed_dir.get_config')
    @patch('code.task_t001b_create_processed_dir.ensure_dirs')
    @patch('code.task_t001b_create_processed_dir.log_info')
    def test_returns_existing_directory(self, mock_log_info, mock_ensure_dirs, mock_get_config):
        """Test that the function returns the existing directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the directory beforehand
            target_path = Path(tmpdir) / 'data' / 'processed'
            target_path.mkdir(parents=True)
            
            # Mock config
            mock_get_config.return_value = {'paths': {'processed': str(target_path)}}
            
            # Call the function
            result = task_module.create_processed_directory()
            
            # Verify it returned the existing path
            assert result == target_path
            assert result.exists()

    @patch('code.task_t001b_create_processed_dir.get_config')
    @patch('code.task_t001b_create_processed_dir.ensure_dirs')
    @patch('code.task_t001b_create_processed_dir.log_error')
    def test_raises_on_os_error(self, mock_log_error, mock_ensure_dirs, mock_get_config):
        """Test that the function raises RuntimeError if mkdir fails."""
        with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            mock_get_config.return_value = {'paths': {'processed': '/root/protected/path'}}
            
            with pytest.raises(RuntimeError, match="Failed to create data/processed directory"):
                task_module.create_processed_directory()
            
            mock_log_error.assert_called()

    @patch('code.task_t001b_create_processed_dir.get_config')
    @patch('code.task_t001b_create_processed_dir.ensure_dirs')
    def test_ensures_base_dirs(self, mock_ensure_dirs, mock_get_config):
        """Test that ensure_dirs is called before creating the specific directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_config.return_value = {'paths': {'processed': str(Path(tmpdir) / 'data' / 'processed')}}
            
            task_module.create_processed_directory()
            
            mock_ensure_dirs.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])