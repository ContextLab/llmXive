"""
Unit tests for Task T001a: Create data directory: data/raw/
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
# Note: We mock the config and utils to ensure isolation
from code.task_t001a_create_raw_dir import create_raw_directory


class TestCreateRawDirectory:
    """Tests for the create_raw_directory function."""

    @patch('code.task_t001a_create_raw_dir.get_config')
    @patch('code.task_t001a_create_raw_dir.ensure_dirs')
    @patch('code.task_t001a_create_raw_dir.log_info')
    def test_creates_directory_if_not_exists(self, mock_log_info, mock_ensure_dirs, mock_get_config):
        """Test that the function creates the directory if it doesn't exist."""
        # Setup mock config
        mock_config = {'paths': {'data': 'data'}}
        mock_get_config.return_value = mock_config

        # Mock Path object
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path_instance.mkdir.return_value = None
        
        with patch('code.task_t001a_create_raw_dir.Path') as mock_path_class:
            mock_path_class.return_value = mock_path_instance
            
            # Execute
            result = create_raw_directory()

            # Assertions
            mock_ensure_dirs.assert_called_once()
            mock_path_instance.exists.assert_called_once()
            mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_log_info.assert_called()
            assert result == mock_path_instance

    @patch('code.task_t001a_create_raw_dir.get_config')
    @patch('code.task_t001a_create_raw_dir.ensure_dirs')
    @patch('code.task_t001a_create_raw_dir.log_info')
    def test_skips_creation_if_exists(self, mock_log_info, mock_ensure_dirs, mock_get_config):
        """Test that the function skips creation if directory already exists."""
        # Setup mock config
        mock_config = {'paths': {'data': 'data'}}
        mock_get_config.return_value = mock_config

        # Mock Path object where exists returns True
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        
        with patch('code.task_t001a_create_raw_dir.Path') as mock_path_class:
            mock_path_class.return_value = mock_path_instance
            
            # Execute
            result = create_raw_directory()

            # Assertions
            mock_ensure_dirs.assert_called_once()
            mock_path_instance.exists.assert_called_once()
            mock_path_instance.mkdir.assert_not_called()
            # Should log that it already exists
            assert any("already exists" in str(call) for call in mock_log_info.call_args_list)

    @patch('code.task_t001a_create_raw_dir.get_config')
    @patch('code.task_t001a_create_raw_dir.ensure_dirs')
    @patch('code.task_t001a_create_raw_dir.log_warning')
    def test_raises_on_os_error(self, mock_log_warning, mock_ensure_dirs, mock_get_config):
        """Test that the function raises OSError if directory creation fails."""
        mock_config = {'paths': {'data': 'data'}}
        mock_get_config.return_value = mock_config

        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path_instance.mkdir.side_effect = OSError("Permission denied")
        
        with patch('code.task_t001a_create_raw_dir.Path') as mock_path_class:
            mock_path_class.return_value = mock_path_instance
            
            # Execute and assert exception
            with pytest.raises(OSError):
                create_raw_directory()

            mock_log_warning.assert_called_once()