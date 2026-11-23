"""
Test suite to verify that all required dependencies in requirements.txt
can be imported and are compatible with the specified versions.
"""
import subprocess
import sys
import importlib
import pytest
from pathlib import Path

# Define expected packages and their versions from requirements.txt
EXPECTED_PACKAGES = {
    "pandas": "2.0.3",
    "numpy": "1.24.3",
    "scikit-learn": "1.3.0",
    "hrv-analysis": "1.1.0",
    "pybids": "0.16.5",
    "requests": "2.31.0",
    "pyyaml": "6.0.1",
    "jsonschema": "4.19.0",
    "statsmodels": "0.14.0",
}

# Mapping of package names to import names (some differ)
IMPORT_MAP = {
    "pandas": "pandas",
    "numpy": "numpy",
    "scikit-learn": "sklearn",
    "hrv-analysis": "hrv",
    "pybids": "pybids",
    "requests": "requests",
    "pyyaml": "yaml",
    "jsonschema": "jsonschema",
    "statsmodels": "statsmodels",
}

@pytest.fixture(scope="module")
def requirements_path():
    return Path(__file__).parent.parent / "requirements.txt"

def test_requirements_file_exists(requirements_path):
    """Assert that requirements.txt exists in the project root."""
    assert requirements_path.exists(), "requirements.txt not found in project root"

def test_all_packages_installable(requirements_path):
    """Assert that all packages listed can be imported after installation."""
    # In a real CI environment, we assume pip install -r requirements.txt ran successfully.
    # This test verifies that the imports work.
    for pkg_name, import_name in IMPORT_MAP.items():
        try:
            importlib.import_module(import_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {pkg_name} (import name: {import_name}): {e}")

def test_package_versions_match(requirements_path):
    """Assert that installed package versions match those in requirements.txt."""
    import importlib.metadata as metadata

    for pkg_name, expected_version in EXPECTED_PACKAGES.items():
        import_name = IMPORT_MAP[pkg_name]
        try:
            # Some packages have different distribution names vs import names
            # e.g., 'scikit-learn' is distributed as 'scikit-learn' but imported as 'sklearn'
            # We need to check the distribution name for version
            dist_name = pkg_name
            version = metadata.version(dist_name)
            assert version == expected_version, (
                f"Version mismatch for {pkg_name}: "
                f"expected {expected_version}, got {version}"
            )
        except metadata.PackageNotFoundError:
            pytest.fail(f"Package {dist_name} not found (import name: {import_name})")