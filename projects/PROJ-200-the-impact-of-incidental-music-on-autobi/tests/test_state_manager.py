"""
Tests for the state_manager module.

These tests verify the checksum tracking and state management functionality.
"""
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# We need to mock the project root for testing
@pytest.fixture
def mock_project_root(tmp_path):
    """Create a temporary directory structure to simulate project root."""
    # Create necessary subdirectories
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "processed").mkdir()
    (tmp_path / "data" / "final").mkdir()
    (tmp_path / "code").mkdir()
    (tmp_path / "tests").mkdir()
    
    # Create a dummy state.yaml
    state_file = tmp_path / "state.yaml"
    state_file.write_text("version: '1.0'\nfiles: {}\n")
    
    return tmp_path

@pytest.fixture
def setup_state_module(mock_project_root):
    """Patch get_project_root to return our temp directory."""
    with patch('code.state_manager.get_project_root', return_value=mock_project_root):
        # We need to reload the module to pick up the patched function
        import importlib
        import code.state_manager
        importlib.reload(code.state_manager)
        yield code.state_manager

def test_calculate_file_checksum(setup_state_module, mock_project_root):
    """Test that checksum calculation works correctly."""
    test_file = mock_project_root / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = setup_state_module._calculate_file_checksum(test_file)
    
    # SHA-256 of "Hello, World!" is known
    expected = "d9013c447cc8b1865767689062d93cd696d929e6f955ccdd7d69c105833d03d3"
    assert checksum == expected

def test_calculate_file_checksum_missing_file(setup_state_module, mock_project_root):
    """Test that checksum raises error for missing file."""
    missing_file = mock_project_root / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        setup_state_module._calculate_file_checksum(missing_file)

def test_load_state_empty_file(setup_state_module, mock_project_root):
    """Test loading an empty state file."""
    state_file = mock_project_root / "state.yaml"
    state_file.write_text("")
    
    state = setup_state_module.load_state()
    
    assert state["version"] == "1.0"
    assert state["files"] == {}

def test_load_state_missing_file(setup_state_module, mock_project_root):
    """Test loading when state file doesn't exist."""
    state_file = mock_project_root / "state.yaml"
    state_file.unlink()
    
    state = setup_state_module.load_state()
    
    assert state["version"] == "1.0"
    assert state["files"] == {}

def test_register_file(setup_state_module, mock_project_root):
    """Test registering a file in the state."""
    test_file = mock_project_root / "data" / "processed" / "test.parquet"
    test_file.write_text("test data")
    
    setup_state_module.register_file(test_file, "Test dataset")
    
    state = setup_state_module.load_state()
    relative_path = str(test_file.relative_to(mock_project_root))
    
    assert relative_path in state["files"]
    assert state["files"][relative_path]["description"] == "Test dataset"
    assert "checksum" in state["files"][relative_path]
    assert "size_bytes" in state["files"][relative_path]

def test_register_missing_file(setup_state_module, mock_project_root):
    """Test that registering a missing file raises an error."""
    missing_file = mock_project_root / "nonexistent.parquet"
    
    with pytest.raises(FileNotFoundError):
        setup_state_module.register_file(missing_file)

def test_verify_file_valid(setup_state_module, mock_project_root):
    """Test verifying a valid file."""
    test_file = mock_project_root / "data" / "processed" / "test.parquet"
    test_file.write_text("test data")
    
    setup_state_module.register_file(test_file)
    result = setup_state_module.verify_file(test_file)
    
    assert result is True

def test_verify_file_modified(setup_state_module, mock_project_root):
    """Test verifying a file that has been modified."""
    test_file = mock_project_root / "data" / "processed" / "test.parquet"
    test_file.write_text("original data")
    
    setup_state_module.register_file(test_file)
    
    # Modify the file
    test_file.write_text("modified data")
    
    result = setup_state_module.verify_file(test_file)
    
    assert result is False

def test_verify_file_missing(setup_state_module, mock_project_root):
    """Test verifying a file that no longer exists."""
    test_file = mock_project_root / "data" / "processed" / "test.parquet"
    test_file.write_text("test data")
    
    setup_state_module.register_file(test_file)
    
    # Delete the file
    test_file.unlink()
    
    result = setup_state_module.verify_file(test_file)
    
    assert result is False

def test_verify_all(setup_state_module, mock_project_root):
    """Test verifying all files in state."""
    file1 = mock_project_root / "data" / "processed" / "file1.parquet"
    file2 = mock_project_root / "data" / "processed" / "file2.parquet"
    
    file1.write_text("data 1")
    file2.write_text("data 2")
    
    setup_state_module.register_file(file1)
    setup_state_module.register_file(file2)
    
    result = setup_state_module.verify_all()
    
    assert result is True

def test_verify_all_with_invalid_file(setup_state_module, mock_project_root):
    """Test verify_all when one file is invalid."""
    file1 = mock_project_root / "data" / "processed" / "file1.parquet"
    file2 = mock_project_root / "data" / "processed" / "file2.parquet"
    
    file1.write_text("data 1")
    file2.write_text("data 2")
    
    setup_state_module.register_file(file1)
    setup_state_module.register_file(file2)
    
    # Modify file2
    file2.write_text("modified data 2")
    
    result = setup_state_module.verify_all()
    
    assert result is False

def test_get_file_info(setup_state_module, mock_project_root):
    """Test getting file info."""
    test_file = mock_project_root / "data" / "processed" / "test.parquet"
    test_file.write_text("test data")
    
    setup_state_module.register_file(test_file, "Test dataset")
    
    info = setup_state_module.get_file_info(test_file)
    
    assert info is not None
    assert info["description"] == "Test dataset"
    assert "checksum" in info

def test_get_file_info_unregistered(setup_state_module, mock_project_root):
    """Test getting info for unregistered file."""
    test_file = mock_project_root / "data" / "processed" / "unregistered.parquet"
    
    info = setup_state_module.get_file_info(test_file)
    
    assert info is None
