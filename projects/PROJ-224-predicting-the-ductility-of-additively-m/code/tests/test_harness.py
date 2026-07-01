"""
Basic test harness to verify project structure and configuration.
These tests ensure that the foundational setup (pytest.ini, requirements, imports)
is correctly configured before running domain-specific tests.
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure the project root is in the path for imports if running from code/tests
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_project_structure_exists():
    """Verify that required top-level directories exist."""
    required_dirs = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "artifacts",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "specs",
    ]
    for dir_path in required_dirs:
        assert dir_path.exists(), f"Required directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"


def test_pytest_config_exists():
    """Verify that pytest.ini exists in the project root."""
    pytest_config = PROJECT_ROOT / "pytest.ini"
    assert pytest_config.exists(), f"pytest.ini not found at {pytest_config}"
    # Basic check that it's not empty
    content = pytest_config.read_text()
    assert len(content) > 0, "pytest.ini is empty"
    assert "[pytest]" in content, "pytest.ini missing [pytest] section"


def test_requirements_exists():
    """Verify that requirements.txt exists and has content."""
    req_file = PROJECT_ROOT / "requirements.txt"
    assert req_file.exists(), f"requirements.txt not found at {req_file}"
    content = req_file.read_text()
    assert len(content) > 0, "requirements.txt is empty"
    # Check for key dependencies mentioned in T006
    required_pkgs = ["pandas", "numpy", "scikit-learn", "statsmodels", "xgboost"]
    content_lower = content.lower()
    for pkg in required_pkgs:
        assert pkg in content_lower, f"Required package '{pkg}' not found in requirements.txt"


def test_imports_work():
    """Verify that core modules can be imported without errors."""
    # Test imports based on the provided API surface
    try:
        from data.acquisition import load_primary_source
        from data.cleaning import convert_units
        from data.preprocessing import calculate_energy_density
        from models.lme_model import fit_lme_model
        from models.xgboost_model import tune_and_train
        from analysis.sensitivity import compute_partial_r2
        from analysis.reporting import generate_final_report
    except ImportError as e:
        pytest.fail(f"Failed to import core module: {e}")


def test_sample_fixture_loads():
    """Verify that the conftest fixtures are available and loadable."""
    # This test ensures that conftest.py is correctly picked up by pytest
    # and that fixtures are defined.
    # We attempt to use the 'add_code_to_path' fixture implicitly by checking
    # if the test environment is set up correctly.
    from tests.conftest import add_code_to_path
    assert callable(add_code_to_path), "add_code_to_path fixture is not callable"