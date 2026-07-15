import pytest
import sys
import os

def test_pytest_timeout_plugin_available():
    """Verify that pytest-timeout plugin is available and configured."""
    try:
        import pytest_timeout
        assert hasattr(pytest_timeout, 'timeout') or 'timeout' in dir(pytest)
    except ImportError:
        pytest.fail("pytest-timeout plugin is not installed. Add 'pytest-timeout' to requirements.txt.")

def test_pytest_cov_plugin_available():
    """Verify that pytest-cov plugin is available for coverage thresholds."""
    try:
        import pytest_cov
        assert hasattr(pytest_cov, 'plugin') or 'cov' in dir(pytest)
    except ImportError:
        pytest.fail("pytest-cov plugin is not installed. Add 'pytest-cov' to requirements.txt.")

def test_code_path_injection():
    """Verify that the 'code' directory is in sys.path for imports."""
    # The conftest.py should handle this, but we verify it works here
    try:
        from src.data.inject import inject_synthetic_signal
        from src.data.validate import check_true_parameters_exist
        assert callable(inject_synthetic_signal)
        assert callable(check_true_parameters_exist)
    except ImportError as e:
        pytest.fail(f"Failed to import from src modules. Check sys.path configuration: {e}")

def test_basic_import():
    """Basic sanity check that the test file itself imports correctly."""
    assert True
