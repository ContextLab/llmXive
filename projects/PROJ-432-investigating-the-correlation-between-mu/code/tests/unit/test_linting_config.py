import os
import subprocess
import sys
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

def test_pyproject_toml_exists(project_root):
    """Verify that pyproject.toml exists in the project root."""
    config_path = project_root / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml must exist for linting configuration."

def test_ruff_config_present(project_root):
    """Verify that ruff configuration is present in pyproject.toml."""
    config_path = project_root / "pyproject.toml"
    content = config_path.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration section missing in pyproject.toml"
    assert "line-length" in content, "Ruff line-length setting missing"

def test_black_config_present(project_root):
    """Verify that black configuration is present in pyproject.toml."""
    config_path = project_root / "pyproject.toml"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Black configuration section missing in pyproject.toml"
    assert "line-length" in content, "Black line-length setting missing"

def test_ruff_check_executable(project_root):
    """Verify that ruff can be executed and reads the config."""
    config_path = project_root / "pyproject.toml"
    try:
        result = subprocess.run(
            ["ruff", "check", "--config", str(config_path), "code/"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect a return code of 0 if no issues, or non-zero if issues exist.
        # The critical part is that it doesn't crash with a config error.
        assert "Failed to load configuration" not in result.stderr
    except FileNotFoundError:
        pytest.skip("Ruff not installed in test environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")

def test_black_check_executable(project_root):
    """Verify that black can be executed and reads the config."""
    config_path = project_root / "pyproject.toml"
    try:
        result = subprocess.run(
            ["black", "--check", "--config", str(config_path), "code/"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect a return code of 0 if formatted correctly, or 1 if not.
        # The critical part is that it doesn't crash with a config error.
        assert "Invalid config" not in result.stderr
    except FileNotFoundError:
        pytest.skip("Black not installed in test environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")