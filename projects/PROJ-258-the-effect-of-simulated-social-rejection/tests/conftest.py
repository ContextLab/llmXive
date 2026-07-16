"""
Pytest configuration and fixtures.
"""
import os
import sys
import pytest

# Ensure the code directory is in the path for imports
# This assumes tests are run from the project root
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code')
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    # Cleanup not strictly necessary for path, but good practice if needed

@pytest.fixture
def sample_results():
    """Fixture providing sample analysis results."""
    return {
        "anova_results": {
            "F": 5.67,
            "p_value": 0.012,
            "p_fdr": 0.024,
            "effect_size": 0.75
        },
        "sensitivity": {
            "0.01": 0.45,
            "0.05": 0.82,
            "0.1": 0.91
        },
        "small_n_warning": "Sample size N=25 is small; confidence intervals may be wide."
    }

@pytest.fixture
def tmp_report_dir(tmp_path):
    """Fixture to create a temporary directory for report files."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return reports_dir
