"""
Tests for project structure initialization.

Verifies that T001a requirements are met:
1. All required directories exist
2. README.md exists and contains required text
"""
import os
import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path("projects/PROJ-444-predicting-molecular-properties-from-top")

@pytest.fixture(autouse=True)
def setup_project_structure():
    """
    Fixture to ensure project structure is set up before tests run.
    This mimics the execution of T001a.
    """
    from code.setup_project_structure import main as setup_main
    # Run the setup script
    setup_main()

def test_required_directories_exist():
    """
    Verify that all required directories from T001a exist.
    """
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests",
        "reports",
        "state",
    ]
    
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_readme_exists_and_content():
    """
    Verify that README.md exists and contains the required text.
    """
    readme_path = PROJECT_ROOT / "README.md"
    assert readme_path.exists(), "README.md does not exist"
    
    content = readme_path.read_text(encoding="utf-8")
    assert "Project: Predicting Molecular Properties from TDA" in content, \
        f"README.md missing required content. Content: {content}"
    assert len(content) > 0, "README.md is empty"

def test_project_root_exists():
    """
    Verify the project root directory exists.
    """
    assert PROJECT_ROOT.exists(), f"Project root does not exist: {PROJECT_ROOT}"
    assert PROJECT_ROOT.is_dir(), f"Project root is not a directory: {PROJECT_ROOT}"
