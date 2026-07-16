"""
Tests to verify the project structure has been created correctly.
"""
import os
import pytest

REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    "specs/001-gene-regulation",
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
    "specs/001-gene-regulation/contracts"
]

def test_directories_exist():
    """Verify that all required project directories exist."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        if not os.path.isdir(dir_path):
            missing.append(dir_path)
    
    assert not missing, f"The following directories are missing: {missing}"

def test_gitkeep_files_exist():
    """Verify that .gitkeep files exist in key directories."""
    required_keeps = [
        "src/.gitkeep",
        "tests/.gitkeep",
        "data/raw/.gitkeep",
        "data/derived/.gitkeep",
        "data/gold_standard/.gitkeep",
        "artifacts/.gitkeep",
        "specs/001-gene-regulation/contracts/.gitkeep"
    ]
    
    missing = []
    for file_path in required_keeps:
        if not os.path.isfile(file_path):
            missing.append(file_path)
    
    assert not missing, f"The following .gitkeep files are missing: {missing}"