import subprocess
import sys
import pytest
from pathlib import Path

def test_flake8_installed():
    """Verify flake8 is installed and can be invoked."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "flake8" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("flake8 is not installed or not callable via python -m flake8")

def test_black_installed():
    """Verify black is installed and can be invoked."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("black is not installed or not callable via python -m black")

def test_isort_installed():
    """Verify isort is installed and can be invoked."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "isort" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("isort is not installed or not callable via python -m isort")

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    root = Path(__file__).parent.parent
    flake8_config = root / ".flake8"
    assert flake8_config.exists(), ".flake8 configuration file is missing"

def test_black_config_exists():
    """Verify pyproject.toml contains black configuration."""
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml is missing"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section missing in pyproject.toml"

def test_project_code_is_flake8_compliant():
    """Run flake8 on the project source code to ensure compliance."""
    root = Path(__file__).parent.parent
    src_dir = root / "src"
    tests_dir = root / "tests"
    scripts_dir = root / "scripts"
    
    # Only check Python files in src, tests, and scripts
    paths_to_check = []
    for directory in [src_dir, tests_dir, scripts_dir]:
        if directory.exists():
            paths_to_check.append(str(directory))
    
    if not paths_to_check:
        pytest.skip("No source directories found to check")
        
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8"] + paths_to_check,
            capture_output=True,
            text=True,
            timeout=60
        )
        # flake8 returns 0 if no issues found, non-zero otherwise
        if result.returncode != 0:
            pytest.fail(f"flake8 found issues:\n{result.stdout}\n{result.stderr}")
    except subprocess.TimeoutExpired:
        pytest.fail("flake8 check timed out")
    except Exception as e:
        pytest.fail(f"Error running flake8: {e}")