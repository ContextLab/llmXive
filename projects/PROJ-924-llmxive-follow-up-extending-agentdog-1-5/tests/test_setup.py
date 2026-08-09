"""
Tests for project setup and directory structure.
Verifies that T001a directories exist.
"""
import os
import pytest
from pathlib import Path


def get_project_root():
    """
    Determine the project root directory.
    Assumes tests are run from the repo root or project root.
    We look for the specific project folder.
    """
    # Try current directory first
    current = Path.cwd()
    project_name = "PROJ-924-llmxive-follow-up-extending-agentdog-1-5"
    
    # Check if current is the project root
    if (current / project_name).exists():
        return current / project_name
    
    # Check if current is inside the project root (e.g. in tests/)
    parent = current
    while parent != parent.parent:
        if (parent / project_name).exists():
            return parent / project_name
        parent = parent.parent
    
    # Fallback: assume current is project root if we are in tests/
    if current.name == "tests":
        return current.parent
    
    return current


def test_directories_exist():
    """
    Verify that all directories created by T001a exist.
    """
    project_root = get_project_root()
    project_name = "PROJ-924-llmxive-follow-up-extending-agentdog-1-5"
    
    # The task specifies creating these relative to the project root (except the project folder itself)
    # But the task description lists `projects/.../code/` as a target.
    # Based on T001a: "Create ... `projects/.../code/`, `tests/`, `data/raw/`..."
    # This implies the structure is:
    # projects/PROJ-.../
    #   code/
    #   tests/
    #   data/...
    #   specs/
    #   docs/
    
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/test",
        "specs",
        "docs",
        "specs/001-llmxive-drift-detection"
    ]
    
    missing = []
    for rel_dir in required_dirs:
        full_path = project_root / rel_dir
        if not full_path.exists():
            missing.append(str(full_path))
    
    assert not missing, f"The following required directories are missing: {missing}"