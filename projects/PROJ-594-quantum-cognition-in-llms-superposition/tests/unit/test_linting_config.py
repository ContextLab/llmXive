"""
Test to verify that linting configuration is correctly set up.
This test ensures that black and flake8 configurations are valid.
"""
import subprocess
import os
import sys
import tempfile
import pytest

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
FLAKE8_CONFIG = os.path.join(PROJECT_ROOT, '.flake8')
BLACK_CONFIG = os.path.join(PROJECT_ROOT, 'pyproject.toml')

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    assert os.path.exists(FLAKE8_CONFIG), f"Missing .flake8 config at {FLAKE8_CONFIG}"

def test_black_config_exists():
    """Verify black configuration exists in pyproject.toml."""
    assert os.path.exists(BLACK_CONFIG), f"Missing pyproject.toml at {BLACK_CONFIG}"
    with open(BLACK_CONFIG, 'r') as f:
        content = f.read()
        assert '[tool.black]' in content, "Missing [tool.black] section in pyproject.toml"

def test_flake8_runs_without_error():
    """Verify flake8 can run on a simple test file."""
    # Create a temporary Python file with intentional style issues
    test_code = """
import os
import sys
def test_func(  ):
    x=1
    return x
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        # Run flake8 on the temp file
        result = subprocess.run(
            ['flake8', '--config=' + FLAKE8_CONFIG, temp_file],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        # flake8 should return non-zero for style issues (expected)
        # The test passes if flake8 runs without crashing
        assert result.returncode != 0, "flake8 should report style issues"
    finally:
        os.unlink(temp_file)

def test_black_format_check():
    """Verify black can check formatting."""
    # Create a temporary Python file with incorrect formatting
    test_code = """
def test_func(  ):
    x=1
    return x
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        # Run black --check on the temp file
        result = subprocess.run(
            ['black', '--config', BLACK_CONFIG, '--check', temp_file],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        # black should return non-zero for unformatted code (expected)
        assert result.returncode != 0, "black should report formatting issues"
    finally:
        os.unlink(temp_file)