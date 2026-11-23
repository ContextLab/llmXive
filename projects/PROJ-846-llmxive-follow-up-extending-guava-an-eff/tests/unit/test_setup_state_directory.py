import os
import tempfile
import pytest
from pathlib import Path
import shutil

# We need to temporarily change the working directory to a temp directory
# to test directory creation without polluting the actual repo root during tests
from code.setup_state_directory import create_state_directory

@pytest.fixture
def temp_repo_root():
    """Create a temporary directory to simulate a repository root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def change_to_temp_dir(temp_repo_root):
    """Change current working directory to the temp repo root."""
    original_cwd = os.getcwd()
    os.chdir(temp_repo_root)
    yield
    os.chdir(original_cwd)

def test_create_state_directory_creates_folder(change_to_temp_dir, temp_repo_root):
    """Test that create_state_directory creates the 'state' folder."""
    state_dir = create_state_directory()
    
    expected_path = temp_repo_root / "state"
    assert state_dir == expected_path
    assert state_dir.exists()
    assert state_dir.is_dir()

def test_create_state_directory_creates_gitkeep(change_to_temp_dir, temp_repo_root):
    """Test that create_state_directory creates a .gitkeep file inside 'state'."""
    create_state_directory()
    
    gitkeep_path = temp_repo_root / "state" / ".gitkeep"
    assert gitkeep_path.exists()
    assert gitkeep_path.is_file()

def test_create_state_directory_idempotent(change_to_temp_dir, temp_repo_root):
    """Test that calling create_state_directory multiple times does not fail."""
    dir1 = create_state_directory()
    dir2 = create_state_directory()
    
    assert dir1 == dir2
    assert (temp_repo_root / "state" / ".gitkeep").exists()