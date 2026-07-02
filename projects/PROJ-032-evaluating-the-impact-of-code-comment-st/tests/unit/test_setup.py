"""
Unit tests for T002: Initialize Python 3.9+ project.

Verifies that requirements files exist and contain expected packages.
"""
import os
import sys
from pathlib import Path

import pytest

# Add src/code to path to allow imports if needed, though this test is file-based
current_dir = Path(__file__).parent
code_dir = current_dir.parent.parent / "src" / "code"

@pytest.fixture
def requirements_path():
    return code_dir / "requirements.txt"

@pytest.fixture
def dev_requirements_path():
    return code_dir / "dev-requirements.txt"

def test_requirements_file_exists(requirements_path):
    """Test that requirements.txt exists."""
    assert requirements_path.exists(), "requirements.txt must exist in src/code/"

def test_dev_requirements_file_exists(dev_requirements_path):
    """Test that dev-requirements.txt exists in src/code/."""
    assert dev_requirements_path.exists(), "dev-requirements.txt must exist in src/code/"

def test_requirements_contains_expected_deps(requirements_path):
    """Test that requirements.txt contains the mandatory runtime dependencies."""
    required_deps = [
        "datasets",
        "tree-sitter",
        "tree-sitter-python",
        "textstat",
        "textblob",
        "pylint",
        "gitpython",
        "scikit-learn",
        "pandas",
        "numpy",
        "statsmodels",
        "radon",
        "psutil"
    ]
    
    content = requirements_path.read_text()
    content_lower = content.lower()
    
    for dep in required_deps:
        # Check if the dependency name is in the file (ignoring version specifiers)
        # We look for the package name at the start of a line or after a newline
        lines = content_lower.split('\n')
        found = False
        for line in lines:
            if line.strip().startswith(dep):
                found = True
                break
        assert found, f"Dependency '{dep}' is missing from requirements.txt"

def test_dev_requirements_contains_expected_deps(dev_requirements_path):
    """Test that dev-requirements.txt contains the mandatory dev dependencies."""
    required_deps = [
        "pip-audit",
        "bandit",
        "pytest",
        "pytest-cov"
    ]
    
    content = dev_requirements_path.read_text()
    content_lower = content.lower()
    
    for dep in required_deps:
        lines = content_lower.split('\n')
        found = False
        for line in lines:
            if line.strip().startswith(dep):
                found = True
                break
        assert found, f"Dev dependency '{dep}' is missing from dev-requirements.txt"

def test_requirements_file_not_empty(requirements_path):
    """Test that requirements.txt is not empty."""
    content = requirements_path.read_text().strip()
    assert len(content) > 0, "requirements.txt should not be empty"

def test_dev_requirements_file_not_empty(dev_requirements_path):
    """Test that dev-requirements.txt is not empty."""
    content = dev_requirements_path.read_text().strip()
    assert len(content) > 0, "dev-requirements.txt should not be empty"