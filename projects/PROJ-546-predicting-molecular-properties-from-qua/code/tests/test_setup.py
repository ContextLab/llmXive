"""
Basic smoke test to verify the project directory structure and test suite setup.
"""
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_directory_structure_exists():
    """Verify that the required test subdirectories exist."""
    assert (PROJECT_ROOT / "tests" / "unit").exists(), "tests/unit directory missing"
    assert (PROJECT_ROOT / "tests" / "integration").exists(), "tests/integration directory missing"
    assert (PROJECT_ROOT / "tests" / "contract").exists(), "tests/contract directory missing"

def test_docs_directory_exists():
    """Verify that the docs directory exists."""
    assert (PROJECT_ROOT / "docs").exists(), "docs directory missing"

def test_readme_exists():
    """Verify that README files exist in test and docs directories."""
    assert (PROJECT_ROOT / "tests" / "README.md").exists(), "tests/README.md missing"
    assert (PROJECT_ROOT / "docs" / "README.md").exists(), "docs/README.md missing"