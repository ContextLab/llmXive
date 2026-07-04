import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from code.setup_state_dir import main


@patch('code.setup_state_dir.Path')
def test_main_creates_directory(mock_path_class):
    """
    Test that main() creates the state directory if it doesn't exist.
    """
    mock_project_root = MagicMock()
    mock_state_dir = MagicMock()
    
    # Configure the mock chain: Path() -> mock_project_root -> / "state" -> mock_state_dir
    mock_path_class.return_value.parent.parent = mock_project_root
    mock_state_dir.__truediv__ = lambda self, name: mock_state_dir if name == "state" else MagicMock()
    
    # Simulate directory not existing
    mock_state_dir.exists.return_value = False
    mock_state_dir.mkdir.return_value = None
    
    # Mock the .gitkeep file check
    mock_gitkeep = MagicMock()
    mock_state_dir.__truediv__.return_value.exists.return_value = False
    mock_state_dir.__truediv__.return_value.write_text.return_value = None
    
    # Run main
    result = main()
    
    # Assertions
    assert result == 0
    mock_state_dir.mkdir.assert_called_once_with(parents=True)
    mock_state_dir.__truediv__.return_value.write_text.assert_called_once()


@patch('code.setup_state_dir.Path')
def test_main_directory_already_exists(mock_path_class):
    """
    Test that main() does nothing if the state directory already exists.
    """
    mock_project_root = MagicMock()
    mock_state_dir = MagicMock()
    
    # Configure the mock chain
    mock_path_class.return_value.parent.parent = mock_project_root
    mock_state_dir.__truediv__ = lambda self, name: mock_state_dir if name == "state" else MagicMock()
    
    # Simulate directory already existing
    mock_state_dir.exists.return_value = True
    
    # Mock the .gitkeep file check
    mock_gitkeep = MagicMock()
    mock_state_dir.__truediv__.return_value.exists.return_value = True
    
    # Run main
    result = main()
    
    # Assertions
    assert result == 0
    mock_state_dir.mkdir.assert_not_called()
    mock_state_dir.__truediv__.return_value.write_text.assert_not_called()