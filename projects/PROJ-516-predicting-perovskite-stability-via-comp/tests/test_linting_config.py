"""
Simple sanity checks to ensure linting tools are installed and can run.
This does not check code style compliance, but verifies the configuration exists
and the tools are callable.
"""
import subprocess
import sys
from pathlib import Path

def test_black_is_available():
    """Verify black is installed and can run --version."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0, "Black is not installed or not working."
    assert "black" in result.stdout.lower()

def test_isort_is_available():
    """Verify isort is installed and can run --version."""
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0, "isort is not installed or not working."
    assert "isort" in result.stdout.lower()

def test_flake8_is_available():
    """Verify flake8 is installed and can run --version."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--version"],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0, "flake8 is not installed or not working."

def test_pylint_is_available():
    """Verify pylint is installed and can run --version."""
    result = subprocess.run(
        [sys.executable, "-m", "pylint", "--version"],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0, "pylint is not installed or not working."

def test_config_files_exist():
    """Verify configuration files exist in the project root."""
    root = Path(__file__).parent.parent
    assert (root / ".flake8").exists(), ".flake8 config missing"
    assert (root / ".pylintrc").exists(), ".pylintrc config missing"
    assert (root / "pyproject.toml").exists(), "pyproject.toml config missing"
    assert (root / ".isort.cfg").exists(), ".isort.cfg config missing"

def test_black_config_in_pyproject():
    """Verify black settings are present in pyproject.toml."""
    root = Path(__file__).parent.parent
    content = (root / "pyproject.toml").read_text()
    assert "[tool.black]" in content, "Black section missing in pyproject.toml"

def test_isort_config_in_isort_cfg():
    """Verify isort settings are present in .isort.cfg."""
    root = Path(__file__).parent.parent
    content = (root / ".isort.cfg").read_text()
    assert "[settings]" in content, "Settings section missing in .isort.cfg"
    assert "profile = black" in content, "isort profile should be set to black"