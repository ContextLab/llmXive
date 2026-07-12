import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_data_structure import create_data_directories, create_gitignore_rules, create_gitkeep_files

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate a project root."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_create_data_directories(temp_project_root):
    """Test that the required data directories are created."""
    created_dirs = create_data_directories(temp_project_root)
    
    # Check that all expected directories were created
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/derived",
        "logs"
    ]
    
    for expected in expected_dirs:
        full_path = Path(temp_project_root) / expected
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_create_gitkeep_files(temp_project_root):
    """Test that .gitkeep files are created in data directories."""
    # First create the directories
    create_data_directories(temp_project_root)
    
    # Then create gitkeep files
    created_keeps = create_gitkeep_files(temp_project_root)
    
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/derived",
        "logs"
    ]
    
    for expected in expected_dirs:
        full_path = Path(temp_project_root) / expected / ".gitkeep"
        assert full_path.exists(), f".gitkeep file at {full_path} was not created"
        assert full_path.is_file(), f"{full_path} is not a file"

def test_create_gitignore_rules(temp_project_root):
    """Test that .gitignore is created/updated with correct rules."""
    gitignore_path = create_gitignore_rules(temp_project_root)
    
    # Verify the file exists
    assert os.path.exists(gitignore_path), ".gitignore file was not created"
    
    # Read the content
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    # Check for required rules
    required_rules = [
        "data/raw/",
        "data/processed/",
        "data/derived/",
        "logs/"
    ]
    
    for rule in required_rules:
        assert rule in content, f"Rule '{rule}' not found in .gitignore"

def test_idempotency(temp_project_root):
    """Test that running the setup multiple times doesn't cause errors or duplicates."""
    # Run setup twice
    create_data_directories(temp_project_root)
    create_gitignore_rules(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    create_data_directories(temp_project_root)
    create_gitignore_rules(temp_project_root)
    create_gitkeep_files(temp_project_root)
    
    # Verify directories still exist
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/derived",
        "logs"
    ]
    
    for expected in expected_dirs:
        full_path = Path(temp_project_root) / expected
        assert full_path.exists(), f"Directory {full_path} missing after multiple runs"
    
    # Verify .gitignore doesn't have duplicate rules
    with open(Path(temp_project_root) / ".gitignore", 'r') as f:
        lines = f.readlines()
    
    # Count occurrences of a specific rule
    rule_count = sum(1 for line in lines if "data/raw/" in line)
    assert rule_count == 1, f"Duplicate rule found in .gitignore (count: {rule_count})"
