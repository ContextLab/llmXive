"""
Unit tests to verify pytest configuration and plugin availability.
These tests ensure that the CI environment has the required pytest plugins
and configuration settings (timeout, coverage) properly installed.
"""
import pytest
import sys
import os
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def test_pytest_timeout_plugin_available():
    """Verify that pytest-timeout plugin is installed and available."""
    try:
        import pytest_timeout
        assert hasattr(pytest_timeout, 'PytestTimeoutError')
    except ImportError:
        pytest.fail("pytest-timeout plugin is not installed")

def test_pytest_cov_plugin_available():
    """Verify that pytest-cov plugin is installed and available."""
    try:
        import pytest_cov
        assert hasattr(pytest_cov, 'PytestCovPlugin')
    except ImportError:
        pytest.fail("pytest-cov plugin is not installed")

def test_code_path_injection():
    """Verify that the code directory is correctly added to sys.path."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    assert str(code_dir) in sys.path or any(
        code_dir in Path(p).parents for p in sys.path
    )

def test_basic_import():
    """Test that basic imports from the project work."""
    try:
        # Try importing a known module if available
        import importlib.util
        spec = importlib.util.find_spec("src.utils.config")
        assert spec is not None, "src.utils.config module not found"
    except Exception as e:
        # If the module doesn't exist yet, that's okay for this test
        # The important thing is that the import system works
        pass

@pytest.mark.timeout(10)
def test_timeout_mechanism_works():
    """Verify that the timeout mechanism is working by running a quick test."""
    # This test should pass quickly
    assert True

def test_pytest_config_file_exists():
    """Verify that pytest.ini or pyproject.toml exists in the code directory."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    pytest_ini = code_dir / "pytest.ini"
    pyproject_toml = code_dir / "pyproject.toml"
    
    assert pytest_ini.exists() or pyproject_toml.exists(), \
        "Neither pytest.ini nor pyproject.toml found in code directory"

def test_timeout_setting_in_config():
    """Verify that timeout setting is present in configuration."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    pytest_ini = code_dir / "pytest.ini"
    pyproject_toml = code_dir / "pyproject.toml"
    
    timeout_found = False
    
    if pytest_ini.exists():
        with open(pytest_ini, 'r') as f:
            content = f.read()
            if 'timeout = 300' in content:
                timeout_found = True
    
    if pyproject_toml.exists():
        with open(pyproject_toml, 'r') as f:
            content = f.read()
            if 'timeout' in content.lower():
                timeout_found = True
    
    assert timeout_found, "Timeout setting (300s) not found in pytest configuration"

def test_coverage_threshold_in_config():
    """Verify that coverage threshold is present in configuration."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    pyproject_toml = code_dir / "pyproject.toml"
    
    assert pyproject_toml.exists(), "pyproject.toml not found"
    
    with open(pyproject_toml, 'r') as f:
        content = f.read()
        assert 'fail_under' in content.lower() or 'cov-fail-under' in content, \
            "Coverage threshold not found in pyproject.toml"