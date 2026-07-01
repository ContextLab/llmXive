"""
Contract test to verify that requirements.txt exists and contains
the required pinned packages for the project.

This test ensures the environment setup task (T002) was completed correctly.
"""
import os
import re
from pathlib import Path

REQUIRED_PACKAGES = {
    'torch',
    'torch-geometric',
    'rdkit',
    'datasets',
    'pandas',
    'scipy',
    'scikit-learn',
}

def test_requirements_file_exists():
    """Verify that code/requirements.txt exists."""
    project_root = Path(__file__).parent.parent.parent
    requirements_path = project_root / 'code' / 'requirements.txt'
    assert requirements_path.exists(), f"requirements.txt not found at {requirements_path}"

def test_requirements_contains_required_packages():
    """Verify that requirements.txt contains all required packages."""
    project_root = Path(__file__).parent.parent.parent
    requirements_path = project_root / 'code' / 'requirements.txt'
    
    with open(requirements_path, 'r') as f:
        content = f.read().lower()
    
    missing_packages = []
    for package in REQUIRED_PACKAGES:
        # Check if package name appears in requirements (case-insensitive)
        pattern = re.compile(rf'^{re.escape(package)}', re.IGNORECASE | re.MULTILINE)
        if not pattern.search(content):
            missing_packages.append(package)
    
    assert len(missing_packages) == 0, f"Missing required packages: {missing_packages}"

def test_requirements_has_version_pins():
    """Verify that packages have version constraints (>= or ==)."""
    project_root = Path(__file__).parent.parent.parent
    requirements_path = project_root / 'code' / 'requirements.txt'
    
    with open(requirements_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    for line in lines:
        # Each line should have a version constraint
        assert '>=' in line or '==' in line or '<=' in line, \
            f"Package '{line}' does not have a version pin"