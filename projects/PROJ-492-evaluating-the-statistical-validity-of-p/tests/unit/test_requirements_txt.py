"""Test that requirements.txt exists and contains expected packages."""
import os
from pathlib import Path

REQUIRED_PACKAGES = [
    'requests',
    'beautifulsoup4',
    'pandas',
    'numpy',
    'scipy',
    'statsmodels',
    'tqdm',
    'pyyaml',
    'jsonschema',
    'psutil',
    'ruff',
    'black',
    'pre-commit',
]

def test_requirements_txt_exists():
    """Verify requirements.txt file exists at project root."""
    requirements_path = Path('requirements.txt')
    assert requirements_path.exists(), "requirements.txt must exist at project root"

def test_requirements_txt_not_empty():
    """Verify requirements.txt has content."""
    requirements_path = Path('requirements.txt')
    content = requirements_path.read_text().strip()
    assert len(content) > 0, "requirements.txt must not be empty"

def test_requirements_txt_contains_expected_packages():
    """Verify requirements.txt contains all expected packages from pyproject.toml."""
    requirements_path = Path('requirements.txt')
    content = requirements_path.read_text().lower()
    
    for package in REQUIRED_PACKAGES:
        assert package.lower() in content, f"Missing package: {package}"

def test_requirements_txt_format():
    """Verify requirements.txt has valid format (one package per line)."""
    requirements_path = Path('requirements.txt')
    lines = requirements_path.read_text().strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Package line should be simple package name, optionally with version specifier
            # e.g., "requests" or "requests>=2.28.0" or "requests==2.28.0"
            assert not line.startswith('-'), f"Invalid line format (flags not allowed): {line}"