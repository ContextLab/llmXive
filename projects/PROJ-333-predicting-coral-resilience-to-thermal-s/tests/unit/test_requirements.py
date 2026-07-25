"""
Unit tests to verify that requirements.txt exists and contains pinned dependencies.
"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REQUIREMENTS_PATH = os.path.join(PROJECT_ROOT, "requirements.txt")

REQUIRED_PACKAGES = {
    "biopython": "1.84",
    "pysam": "0.22.1",
    "scipy": "1.13.1",
    "pandas": "2.2.2",
    "matplotlib": "3.9.0",
    "gprofiler-official": "1.0.0",
    "rpy2": "3.5.16",
}

def test_requirements_file_exists():
    """Verify that requirements.txt exists in the project root."""
    assert os.path.isfile(REQUIREMENTS_PATH), f"requirements.txt not found at {REQUIREMENTS_PATH}"

def test_requirements_contains_pinned_dependencies():
    """Verify that all required packages are present and pinned to specific versions."""
    with open(REQUIREMENTS_PATH, "r") as f:
        content = f.read()

    missing_packages = []
    for package, version in REQUIRED_PACKAGES.items():
        # Regex to match package==version, allowing for potential comments or whitespace
        pattern = rf"^{re.escape(package)}=={re.escape(version)}"
        if not re.search(pattern, content, re.MULTILINE):
            missing_packages.append(f"{package}=={version}")

    assert not missing_packages, f"Missing or unpinned dependencies in requirements.txt: {missing_packages}"

def test_no_placeholder_versions():
    """Ensure no generic version specifiers like >= or ==0.0.0 are used for core packages."""
    with open(REQUIREMENTS_PATH, "r") as f:
        content = f.read()

    for package in REQUIRED_PACKAGES:
        # Check for loose constraints
        loose_patterns = [
            rf"^{re.escape(package)}>=",
            rf"^{re.escape(package)}<=",
            rf"^{re.escape(package)}~=",
            rf"^{re.escape(package)}==0\.0\.0",
            rf"^{re.escape(package)}==\*",
        ]
        for pattern in loose_patterns:
            if re.search(pattern, content, re.MULTILINE):
                assert False, f"Found loose or placeholder version constraint for {package}"