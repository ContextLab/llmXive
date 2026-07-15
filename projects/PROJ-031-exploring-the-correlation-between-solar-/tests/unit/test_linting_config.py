"""
Unit tests for the linting configuration module.

These tests verify that the configuration script exists and has the
expected structure, without actually running the external tools
(which require network access or specific installed binaries).
"""

import importlib.util
import os
import sys
import pytest

# Path to the module being tested
MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "code", "config", "linting.py"
)

@pytest.fixture
def linting_module():
    """Load the linting module dynamically."""
    spec = importlib.util.spec_from_file_location("linting", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_linting_module_exists():
    """Test that the linting module file exists."""
    assert os.path.exists(MODULE_PATH), f"Module file not found at {MODULE_PATH}"

def test_run_command_function_exists(linting_module):
    """Test that the run_command function is defined."""
    assert hasattr(linting_module, "run_command"), "run_command function not found"
    assert callable(linting_module.run_command), "run_command is not callable"

def test_check_linting_function_exists(linting_module):
    """Test that the check_linting function is defined."""
    assert hasattr(linting_module, "check_linting"), "check_linting function not found"
    assert callable(linting_module.check_linting), "check_linting is not callable"

def test_format_code_function_exists(linting_module):
    """Test that the format_code function is defined."""
    assert hasattr(linting_module, "format_code"), "format_code function not found"
    assert callable(linting_module.format_code), "format_code is not callable"

def test_main_function_exists(linting_module):
    """Test that the main function is defined."""
    assert hasattr(linting_module, "main"), "main function not found"
    assert callable(linting_module.main), "main is not callable"

def test_run_command_returns_bool_on_success(linting_module, monkeypatch):
    """Test that run_command returns True when subprocess succeeds."""
    # Mock subprocess.run to return a completed process with code 0
    class MockResult:
        returncode = 0
    
    def mock_run(*args, **kwargs):
        if kwargs.get('check', False) and 'check=True' in str(args):
            return MockResult()
        return MockResult()
    
    monkeypatch.setattr("subprocess.run", mock_run)
    
    result = linting_module.run_command(["echo", "test"], "Test Check")
    assert result is True

def test_run_command_returns_false_on_failure(linting_module, monkeypatch):
    """Test that run_command returns False when subprocess fails."""
    import subprocess
    
    # Mock subprocess.run to raise CalledProcessError
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["test"])
    
    monkeypatch.setattr("subprocess.run", mock_run)
    
    result = linting_module.run_command(["fail_cmd"], "Test Fail")
    assert result is False
