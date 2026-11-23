"""
Unit tests to verify that linting and formatting configurations are present
and that the tools can be invoked successfully.
"""
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def code_dir(project_root):
    """Return the code directory where config files are located."""
    return project_root / "code"


def test_flake8_config_exists(code_dir):
    """Verify that .flake8 configuration file exists."""
    flake8_config = code_dir / ".flake8"
    assert flake8_config.exists(), f".flake8 config file missing at {flake8_config}"
    assert flake8_config.stat().st_size > 0, ".flake8 config file is empty"


def test_pyproject_toml_exists(code_dir):
    """Verify that pyproject.toml with Black configuration exists."""
    pyproject = code_dir / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml missing at {pyproject}"
    assert pyproject.stat().st_size > 0, "pyproject.toml is empty"

    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"


def test_flake8_can_run(code_dir):
    """Verify that flake8 can be executed against the code directory."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        cwd=code_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"flake8 failed to run: {result.stderr}"


def test_black_can_run(code_dir):
    """Verify that black can be executed and check configuration."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        cwd=code_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"black failed to run: {result.stderr}"

    # Verify black can read the config by doing a dry run on a dummy file
    dummy_file = code_dir / "dummy_check.py"
    try:
        dummy_file.write_text("x=1\n")
        check_result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", "dummy_check.py"],
            cwd=code_dir,
            capture_output=True,
            text=True
        )
        # Black will return 1 if file needs formatting, which is expected for dummy
        # We just verify it runs without crashing
        assert check_result.returncode in [0, 1], f"black check failed unexpectedly: {check_result.stderr}"
    finally:
        if dummy_file.exists():
            dummy_file.unlink()


def test_isort_can_run(code_dir):
    """Verify that isort can be executed."""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        cwd=code_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"isort failed to run: {result.stderr}"