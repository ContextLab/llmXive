import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from code.task_t001e_create_stimuli_dir import create_stimuli_directory, main
from code.config import get_config

@patch('code.task_t001e_create_stimuli_dir.get_config')
@patch('code.task_t001e_create_stimuli_dir.ensure_dirs')
@patch('code.task_t001e_create_stimuli_dir.log_info')
def test_create_stimuli_directory_success(mock_log_info, mock_ensure_dirs, mock_get_config, tmp_path):
    """Test that create_stimuli_directory successfully creates the directory."""
    # Setup mock config
    mock_config = {'base_dir': tmp_path}
    mock_get_config.return_value = mock_config
    
    # Mock ensure_dirs to just create the directory (simulate success)
    def side_effect(path):
        path.mkdir(parents=True, exist_ok=True)
    
    mock_ensure_dirs.side_effect = side_effect

    # Execute
    result_path = create_stimuli_directory()

    # Assert
    expected_path = tmp_path / 'data' / 'stimuli'
    assert result_path == expected_path
    assert result_path.exists()
    assert result_path.is_dir()
    mock_ensure_dirs.assert_called_once_with(expected_path)
    mock_log_info.assert_called()

@patch('code.task_t001e_create_stimuli_dir.get_config')
@patch('code.task_t001e_create_stimuli_dir.ensure_dirs')
@patch('code.task_t001e_create_stimuli_dir.log_error')
def test_create_stimuli_directory_failure(mock_log_error, mock_ensure_dirs, mock_get_config, tmp_path):
    """Test that create_stimuli_directory raises OSError on failure."""
    mock_config = {'base_dir': tmp_path}
    mock_get_config.return_value = mock_config
    
    # Mock ensure_dirs to raise an error
    mock_ensure_dirs.side_effect = OSError("Permission denied")

    # Execute and assert exception
    with pytest.raises(OSError):
        create_stimuli_directory()
    
    mock_log_error.assert_called()

@patch('code.task_t001e_create_stimuli_dir.create_stimuli_directory')
@patch('code.task_t001e_create_stimuli_dir.log_info')
@patch('code.task_t001e_create_stimuli_dir.log_error')
@patch('code.task_t001e_create_stimuli_dir.sys')
def test_main_success(mock_sys, mock_log_error, mock_log_info, mock_create_stimuli_directory, tmp_path):
    """Test that main() runs successfully and exits with 0."""
    mock_create_stimuli_directory.return_value = tmp_path / 'data' / 'stimuli'
    
    main()
    
    mock_create_stimuli_directory.assert_called_once()
    mock_sys.exit.assert_called_with(0)
    mock_log_error.assert_not_called()

@patch('code.task_t001e_create_stimuli_dir.create_stimuli_directory')
@patch('code.task_t001e_create_stimuli_dir.log_error')
@patch('code.task_t001e_create_stimuli_dir.sys')
def test_main_failure(mock_sys, mock_log_error, mock_create_stimuli_directory, tmp_path):
    """Test that main() handles exceptions and exits with 1."""
    mock_create_stimuli_directory.side_effect = Exception("Something went wrong")
    
    main()
    
    mock_create_stimuli_directory.assert_called_once()
    mock_sys.exit.assert_called_with(1)
    mock_log_error.assert_called()