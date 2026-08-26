"""
Unit tests for the setup_data_dirs module.

These tests verify that the data directory structure and .gitkeep files
are created correctly by the setup_data_dirs module.
"""
import os
import tempfile
import pytest
from code.setup_data_dirs import ensure_gitkeep, DATA_SUBDIRS

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_ensure_gitkeep_creates_directory(temp_project_root):
    """Test that ensure_gitkeep creates the directory if it doesn't exist."""
    test_dir = os.path.join(temp_project_root, "test_dir")
    assert not os.path.exists(test_dir)
    
    result = ensure_gitkeep(test_dir)
    
    assert result is True
    assert os.path.exists(test_dir)
    assert os.path.isdir(test_dir)

def test_ensure_gitkeep_creates_gitkeep(temp_project_root):
    """Test that ensure_gitkeep creates the .gitkeep file."""
    test_dir = os.path.join(temp_project_root, "test_dir")
    
    result = ensure_gitkeep(test_dir)
    
    assert result is True
    gitkeep_path = os.path.join(test_dir, ".gitkeep")
    assert os.path.exists(gitkeep_path)
    assert os.path.isfile(gitkeep_path)
    
    # Verify file content
    with open(gitkeep_path, 'r') as f:
        content = f.read()
    assert "Git keep file" in content

def test_ensure_gitkeep_idempotent(temp_project_root):
    """Test that calling ensure_gitkeep multiple times is safe."""
    test_dir = os.path.join(temp_project_root, "test_dir")
    
    # First call
    result1 = ensure_gitkeep(test_dir)
    assert result1 is True
    
    # Second call
    result2 = ensure_gitkeep(test_dir)
    assert result2 is True
    
    # Third call
    result3 = ensure_gitkeep(test_dir)
    assert result3 is True
    
    # Verify only one .gitkeep file exists
    gitkeep_path = os.path.join(test_dir, ".gitkeep")
    assert os.path.exists(gitkeep_path)

def test_ensure_gitkeep_existing_directory(temp_project_root):
    """Test that ensure_gitkeep works when directory already exists."""
    test_dir = os.path.join(temp_project_root, "existing_dir")
    os.makedirs(test_dir, exist_ok=True)
    
    result = ensure_gitkeep(test_dir)
    
    assert result is True
    assert os.path.exists(test_dir)
    gitkeep_path = os.path.join(test_dir, ".gitkeep")
    assert os.path.exists(gitkeep_path)

def test_data_subdirs_defined():
    """Test that the required data subdirectories are defined."""
    assert len(DATA_SUBDIRS) > 0
    assert "data/raw" in DATA_SUBDIRS
    assert "data/generated" in DATA_SUBDIRS
    assert "data/results" in DATA_SUBDIRS

def test_main_success(temp_project_root, monkeypatch):
    """Test that main() returns 0 on success."""
    # Change to temp directory to simulate project root
    monkeypatch.chdir(temp_project_root)
    
    # Create code directory to simulate project structure
    os.makedirs("code", exist_ok=True)
    
    # Import and run main
    import sys
    from code.setup_data_dirs import main
    
    # We need to temporarily change the working directory behavior
    # since main() relies on os.getcwd()
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        result = main()
        assert result == 0
        
        # Verify directories were created
        for subdir in DATA_SUBDIRS:
            full_path = os.path.join(temp_project_root, subdir)
            assert os.path.exists(full_path)
            gitkeep_path = os.path.join(full_path, ".gitkeep")
            assert os.path.exists(gitkeep_path)
    finally:
        os.chdir(original_cwd)