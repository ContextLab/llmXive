"""
Unit tests for the quickstart validation script.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from scripts.validate_quickstart import (
    check_file_exists,
    check_file_not_empty,
    run_command,
    validate_quickstart
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

def test_check_file_exists(temp_dir):
    """Test check_file_exists function."""
    # Test with existing file
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert check_file_exists(test_file) is True

    # Test with non-existing file
    non_existing = temp_dir / "non_existing.txt"
    assert check_file_exists(non_existing) is False

def test_check_file_not_empty(temp_dir):
    """Test check_file_not_empty function."""
    # Test with non-empty file
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert check_file_not_empty(test_file) is True

    # Test with empty file
    empty_file = temp_dir / "empty.txt"
    empty_file.write_text("")
    assert check_file_not_empty(empty_file) is False

def test_run_command_success(temp_dir):
    """Test run_command function with successful execution."""
    # Test with a simple command
    stdout, rc = run_command(["echo", "hello"], cwd=temp_dir)
    assert rc == 0
    assert "hello" in stdout

def test_run_command_failure(temp_dir):
    """Test run_command function with failed execution."""
    # Test with a command that should fail
    stdout, rc = run_command(["false"], cwd=temp_dir)
    assert rc != 0

@patch("scripts.validate_quickstart.check_file_exists")
@patch("scripts.validate_quickstart.check_file_not_empty")
@patch("scripts.validate_quickstart.run_command")
def test_validate_quickstart_missing_file(mock_run, mock_not_empty, mock_exists, temp_dir):
    """Test validate_quickstart when quickstart.md is missing."""
    mock_exists.return_value = False
    
    # Create a minimal project structure
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    
    # Patch Path operations
    with patch("scripts.validate_quickstart.Path") as mock_path:
        mock_path.return_value.__truediv__.return_value = docs_dir / "quickstart.md"
        mock_path.return_value.parent.parent.parent = temp_dir
        
        result = validate_quickstart()
        assert result is False

@patch("scripts.validate_quickstart.check_file_exists")
@patch("scripts.validate_quickstart.check_file_not_empty")
def test_validate_quickstart_empty_file(mock_not_empty, mock_exists, temp_dir):
    """Test validate_quickstart when quickstart.md is empty."""
    mock_exists.return_value = True
    mock_not_empty.return_value = False
    
    # Create a minimal project structure
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    
    # Patch Path operations
    with patch("scripts.validate_quickstart.Path") as mock_path:
        mock_path.return_value.__truediv__.return_value = docs_dir / "quickstart.md"
        mock_path.return_value.parent.parent.parent = temp_dir
        
        result = validate_quickstart()
        assert result is False

@patch("scripts.validate_quickstart.check_file_exists")
@patch("scripts.validate_quickstart.check_file_not_empty")
@patch("scripts.validate_quickstart.run_command")
def test_validate_quickstart_full_success(mock_run, mock_not_empty, mock_exists, temp_dir):
    """Test validate_quickstart with all checks passing."""
    # Mock all checks to pass
    mock_exists.return_value = True
    mock_not_empty.return_value = True
    mock_run.return_value = ("", 0)
    
    # Create a minimal project structure
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "quickstart.md").write_text("test")
    
    requirements_dir = temp_dir
    (requirements_dir / "requirements.txt").write_text("pytest")
    
    code_dir = temp_dir / "code"
    code_dir.mkdir()
    (code_dir / "ingest.py").write_text("print('test')")
    (code_dir / "eda.py").write_text("print('test')")
    (code_dir / "modeling.py").write_text("print('test')")
    
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "results").mkdir()
    
    # Patch Path operations
    with patch("scripts.validate_quickstart.Path") as mock_path:
        # Setup the mock to return our temp directory structure
        mock_path_instance = MagicMock()
        mock_path_instance.__truediv__.side_effect = lambda x: temp_dir / x
        mock_path_instance.parent.parent.parent = temp_dir
        mock_path.return_value = mock_path_instance
        
        result = validate_quickstart()
        assert result is True