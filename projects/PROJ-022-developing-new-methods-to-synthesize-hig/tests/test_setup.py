"""
Test suite to verify directory structure setup.
"""
import os
import pytest
from pathlib import Path

# Required directories that must exist after setup
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/reports",
    "tests",
    "artifacts",
    "code/ingestion",
    "code/features",
    "code/modeling",
    "code/screening",
    "code/reporting",
    "code/utils",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def test_required_directories_exist():
    """Verify all required directories exist."""
    base_path = Path(__file__).parent.parent
    missing_dirs = []
    
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        elif not full_path.is_dir():
            missing_dirs.append(f"{dir_path} (not a directory)")
    
    assert not missing_dirs, f"Missing directories: {missing_dirs}"

def test_gitkeep_files_exist():
    """Verify .gitkeep files exist in data directories."""
    base_path = Path(__file__).parent.parent
    gitkeep_paths = [
        base_path / "data/raw/.gitkeep",
        base_path / "data/processed/.gitkeep",
        base_path / "data/reports/.gitkeep",
        base_path / "artifacts/.gitkeep",
    ]
    
    missing_gitkeeps = []
    for path in gitkeep_paths:
        if not path.exists():
            missing_gitkeeps.append(str(path))
    
    assert not missing_gitkeeps, f"Missing .gitkeep files: {missing_gitkeeps}"

def test_gitignore_exists():
    """Verify .gitignore file exists at project root."""
    base_path = Path(__file__).parent.parent
    gitignore_path = base_path / ".gitignore"
    
    assert gitignore_path.exists(), ".gitignore file not found at project root"
    assert gitignore_path.is_file(), ".gitignore is not a file"

def test_gitignore_contains_required_patterns():
    """Verify .gitignore contains required ignore patterns."""
    base_path = Path(__file__).parent.parent
    gitignore_path = base_path / ".gitignore"
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    required_patterns = [
        "data/raw/*",
        "data/processed/*",
        "*.pkl",
        "__pycache__",
        "*.log"
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    assert not missing_patterns, f"Missing patterns in .gitignore: {missing_patterns}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])