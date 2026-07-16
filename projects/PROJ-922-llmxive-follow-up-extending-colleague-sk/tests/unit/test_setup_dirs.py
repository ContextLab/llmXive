"""
Unit tests for the directory setup script (T001a).
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the config to use a temporary directory for testing
# to avoid polluting the actual project root during unit tests.
import sys
import importlib

@pytest.fixture
def temp_project_root(tmp_path):
    """Creates a temporary directory to act as the project root."""
    return tmp_path

@pytest.fixture
def mock_config(temp_project_root):
    """Mocks the utils.config module to return our temp root."""
    with patch('code.scripts.setup_dirs.get_project_root', return_value=temp_project_root) as mock_root:
        with patch('code.scripts.setup_dirs.ensure_dir') as mock_ensure:
            # Mock ensure_dir to actually create the directory so we can verify existence
            def real_ensure_dir(path):
                path.mkdir(parents=True, exist_ok=True)
            
            mock_ensure.side_effect = real_ensure_dir
            yield mock_root, mock_ensure

def test_create_directories_structure(mock_config, temp_project_root):
    """
    Verifies that create_directories creates all required paths.
    """
    # Import the function after patching
    from code.scripts.setup_dirs import create_directories

    # Execute
    result = create_directories()

    # Assert result
    assert result is True

    # Define expected paths
    expected_dirs = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state/projects/PROJ-922"
    ]

    # Verify existence
    for rel_path in expected_dirs:
        full_path = temp_project_root / rel_path
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"Path {full_path} exists but is not a directory."

def test_main_success(mock_config, temp_project_root, caplog):
    """
    Verifies that main() returns 0 on success.
    """
    from code.scripts.setup_dirs import main
    
    # Capture logs if needed, though main usually returns exit code
    exit_code = main()
    
    assert exit_code == 0