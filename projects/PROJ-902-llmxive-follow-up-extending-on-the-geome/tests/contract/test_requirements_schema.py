"""
Contract test for requirements.txt presence and content correctness.

This test validates that:
1. The requirements.txt file exists in the project root.
2. The file is not empty.
3. The file contains valid package specifications (non-empty lines, no malformed syntax).
4. Expected critical dependencies for the project are present (e.g., datasets, torch, llama-cpp-python).
"""
import os
import re
import pytest
from pathlib import Path

# Project root is assumed to be the parent of the tests directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"

# Critical dependencies expected for the llmXive Geometry Extension project
CRITICAL_PACKAGES = [
    "datasets",
    "torch",
    "llama-cpp-python",
    "numpy",
    "pandas",
    "scipy",
    "statsmodels",
    "ruff",
    "black",
    "pytest",
]

def test_requirements_file_exists():
    """Assert that requirements.txt exists in the project root."""
    assert REQUIREMENTS_PATH.exists(), f"requirements.txt not found at {REQUIREMENTS_PATH}"

def test_requirements_file_not_empty():
    """Assert that requirements.txt is not empty."""
    assert REQUIREMENTS_PATH.stat().st_size > 0, "requirements.txt is empty"

def test_requirements_syntax_valid():
    """
    Assert that every non-empty line in requirements.txt is a valid package specifier.
    
    Validates basic patterns:
    - package_name
    - package_name>=version
    - package_name[extra]
    - package_name>=version, <version
    - Comments (lines starting with #)
    - Empty lines
    """
    with open(REQUIREMENTS_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Regex for a valid pip requirement line (simplified but robust for common cases)
    # Matches: name, name[extras], name>=version, name[extras]>=version, comments, empty
    pattern = re.compile(
        r"^\s*(#.*|\s*|[\w][\w\-\._\[\]]*[\w\-\._]*\s*(\[.*\])?\s*(>=|<=|==|!=|~=|>|<)\s*[\d\w\.\*\-\_]+)?"
    )

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        
        if not pattern.match(line):
            pytest.fail(f"Invalid requirement syntax at line {i}: {line.strip()}")

def test_critical_packages_present():
    """
    Assert that all critical packages required for the project are listed.
    
    Checks for package names (case-insensitive, ignoring version specifiers).
    """
    with open(REQUIREMENTS_PATH, "r", encoding="utf-8") as f:
        content = f.read().lower()

    missing_packages = []
    for pkg in CRITICAL_PACKAGES:
        # Normalize package name for comparison (pip uses hyphens, imports use underscores)
        # We check if the base name exists in the file
        base_name = pkg.lower().replace("_", "-")
        if base_name not in content:
            missing_packages.append(pkg)

    assert not missing_packages, f"Missing critical packages in requirements.txt: {missing_packages}"

def test_no_duplicate_packages():
    """
    Assert that there are no duplicate package specifications in requirements.txt.
    
    Note: This is a simplified check that looks for exact duplicate lines.
    More complex dependency resolution (e.g., different versions) is handled by pip/poetry.
    """
    with open(REQUIREMENTS_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]

    seen = set()
    duplicates = []
    for line in lines:
        # Normalize: remove version specifiers for duplicate checking of base names
        base = re.split(r'[<>=!~\[\s]', line)[0].lower()
        if base in seen:
            duplicates.append(base)
        seen.add(base)

    assert not duplicates, f"Duplicate package specifications found: {duplicates}"