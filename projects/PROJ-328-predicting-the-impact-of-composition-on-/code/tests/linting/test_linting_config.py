"""
Contract tests for linting and formatting configuration.
These tests ensure that flake8 and black are properly configured
and can parse the project's configuration files.
"""
import subprocess
import os
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get the project root directory (parent of code/)."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def code_dir(project_root):
    """Get the code directory."""
    return project_root / "code"


def test_flake8_config_exists(code_dir):
    """Test that flake8 configuration file exists."""
    flake8_configs = [
        code_dir / ".flake8",
        code_dir / "setup.cfg",
        code_dir / "tox.ini"
    ]
    
    assert any(config.exists() for config in flake8_configs), (
        "No flake8 configuration file found. "
        "Create .flake8, setup.cfg, or tox.ini with [flake8] section."
    )


def test_pyproject_toml_exists(code_dir):
    """Test that pyproject.toml exists (required for Black configuration)."""
    pyproject_path = code_dir / "pyproject.toml"
    assert pyproject_path.exists(), (
        "pyproject.toml not found. "
        "Create pyproject.toml with [tool.black] section."
    )


def test_black_can_parse_config(code_dir):
    """Test that Black can successfully parse the configuration."""
    pyproject_path = code_dir / "pyproject.toml"
    
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not found, skipping Black config test")
    
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "--config", str(pyproject_path), str(code_dir / "seed.py")],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black returns 0 if files are formatted correctly, 1 if they need formatting
        # We only care that it can parse the config without errors
        assert "Error:" not in result.stderr, f"Black failed to parse config: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed, skipping config test")
    except subprocess.TimeoutExpired:
        pytest.fail("Black config parsing timed out")


def test_flake8_can_parse_config(code_dir):
    """Test that flake8 can successfully parse the configuration."""
    flake8_path = code_dir / ".flake8"
    
    if not flake8_path.exists():
        # Try setup.cfg
        flake8_path = code_dir / "setup.cfg"
        
    if not flake8_path.exists():
        pytest.skip("No flake8 configuration found, skipping config test")
    
    try:
        result = subprocess.run(
            ["flake8", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            pytest.skip("flake8 not installed or not working, skipping config test")
        
        # Try to run flake8 with our config on a dummy file
        result = subprocess.run(
            ["flake8", "--config", str(flake8_path), "--select=E9,F63,F7,F82", str(code_dir / "seed.py")],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # If we get here without an exception, flake8 parsed the config successfully
        # The return code might be non-zero if there are errors, but that's okay for this test
        assert "SyntaxError" not in result.stderr, f"flake8 failed to parse config: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("flake8 not installed, skipping config test")
    except subprocess.TimeoutExpired:
        pytest.fail("flake8 config parsing timed out")


def test_linting_rules_are_reasonable(code_dir):
    """Test that the configured linting rules are reasonable."""
    # Check that max-line-length is set to a reasonable value (<= 120)
    config_files = [
        code_dir / ".flake8",
        code_dir / "setup.cfg",
        code_dir / "pyproject.toml"
    ]
    
    found_max_line_length = False
    for config_file in config_files:
        if config_file.exists():
            content = config_file.read_text()
            if "max-line-length" in content or "line-length" in content:
                found_max_line_length = True
                # Extract the value (simple regex-like check)
                import re
                match = re.search(r'[Mm]ax[_-]?[Ll]ine[_-]?[Ll]ength[=:]\s*(\d+)', content)
                if match:
                    value = int(match.group(1))
                    assert value <= 120, f"Max line length ({value}) is too high (should be <= 120)"
                    break
    
    assert found_max_line_length, "No max-line-length configuration found"