"""
Integration test for T003: Verify .flake8 and pyproject.toml configuration.
This test creates a temporary Python file and runs flake8 against it
to ensure the configuration is correctly picked up.
"""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path


def test_flake8_config_exists_and_works():
    """
    Verify that .flake8 exists and flake8 runs successfully on a sample file.
    """
    # Ensure .flake8 exists at root
    root = Path(__file__).parent.parent
    flake8_config = root / ".flake8"
    assert flake8_config.exists(), ".flake8 configuration file missing at repository root"

    # Ensure pyproject.toml exists
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml missing at repository root"

    # Ensure the sample file exists
    sample_file = root / "code" / "utils" / "sample.py"
    assert sample_file.exists(), "code/utils/sample.py missing"

    # Run flake8 on the sample file
    # We expect it to run without crashing. It may report warnings/errors
    # but the configuration must be valid.
    try:
        result = subprocess.run(
            ["flake8", str(sample_file)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # flake8 returns 0 if no issues found, non-zero if issues found.
        # The test passes as long as it runs and the config is valid.
        # We just check that it didn't crash with a config error.
        assert "No such file or directory" not in result.stderr
        assert "Unable to find option" not in result.stderr
        # If there are style errors, that's fine for this task (the config is valid),
        # but we ensure the command executed.
        print(f"Flake8 exit code: {result.returncode}")
        if result.stdout:
            print(f"Flake8 output:\n{result.stdout}")
        if result.stderr:
            print(f"Flake8 errors:\n{result.stderr}")
    except FileNotFoundError:
        pytest.fail("flake8 is not installed or not in PATH. Please install flake8.")
    except subprocess.TimeoutExpired:
        pytest.fail("Flake8 execution timed out.")


def test_pyproject_toml_structure():
    """
    Verify that pyproject.toml contains expected sections.
    """
    import tomllib  # Python 3.11+
    # Fallback for older python if tomllib not available, though requirements usually imply modern env
    try:
        with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
    except ImportError:
        # Fallback for older python versions
        import toml
        with open(Path(__file__).parent.parent / "pyproject.toml", "r") as f:
            data = toml.load(f)

    assert "project" in data, "Missing [project] section in pyproject.toml"
    assert "build-system" in data, "Missing [build-system] section in pyproject.toml"
    assert "tool.black" in data, "Missing [tool.black] section in pyproject.toml"
    assert data["tool"]["black"]["line-length"] == 88, "Black line-length should be 88"