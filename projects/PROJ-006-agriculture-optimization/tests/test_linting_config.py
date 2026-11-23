import os
import subprocess
import sys
from pathlib import Path
import pytest

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def test_black_is_installed() -> None:
    """Verify black is installed."""
    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pytest.fail("black is not installed or not working")

def test_flake8_is_installed() -> None:
    """Verify flake8 is installed."""
    try:
        subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pytest.fail("flake8 is not installed or not working")

def test_isort_is_installed() -> None:
    """Verify isort is installed."""
    try:
        subprocess.run(
            [sys.executable, "-m", "isort", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pytest.fail("isort is not installed or not working")

def test_gitignore_exists() -> None:
    """Verify .gitignore exists in project root."""
    root = get_project_root()
    gitignore = root / ".gitignore"
    assert gitignore.exists(), ".gitignore not found in project root"

def test_setup_cfg_exists() -> None:
    """Verify setup.cfg exists (for flake8 config if needed, though we use .flake8)."""
    # Note: We use .flake8 file instead of setup.cfg for flake8 config
    # This test is kept for structural completeness but may be skipped if .flake8 is used
    root = get_project_root()
    setup_cfg = root / "setup.cfg"
    # We allow this to pass if .flake8 exists instead
    flake8_file = root / ".flake8"
    if not setup_cfg.exists() and flake8_file.exists():
        return
    assert setup_cfg.exists() or flake8_file.exists(), "Neither setup.cfg nor .flake8 found"

def test_pyproject_toml_exists() -> None:
    """Verify pyproject.toml exists in project root."""
    root = get_project_root()
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found in project root"

def test_requirements_txt_includes_dev_tools() -> None:
    """Verify requirements.txt includes dev tools (black, flake8, isort, pytest)."""
    root = get_project_root()
    requirements = root / "requirements.txt"
    assert requirements.exists(), "requirements.txt not found"

    content = requirements.read_text()
    required_dev_tools = ["black", "flake8", "isort", "pytest"]
    for tool in required_dev_tools:
        assert tool.lower() in content.lower(), f"{tool} not found in requirements.txt"

def test_code_passes_flake8() -> None:
    """Verify code passes flake8 checks."""
    root = get_project_root()
    src_dir = root / "src"
    if not src_dir.exists():
        pytest.skip("src directory not found, skipping flake8 check")

    result = subprocess.run(
        [sys.executable, "-m", "flake8", str(src_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"flake8 found violations:\n{result.stdout}\n{result.stderr}")

def test_code_passes_isort() -> None:
    """Verify code passes isort checks."""
    root = get_project_root()
    src_dir = root / "src"
    if not src_dir.exists():
        pytest.skip("src directory not found, skipping isort check")

    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check", str(src_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"isort found violations:\n{result.stdout}\n{result.stderr}")

def test_code_passes_black() -> None:
    """Verify code passes black checks."""
    root = get_project_root()
    src_dir = root / "src"
    if not src_dir.exists():
        pytest.skip("src directory not found, skipping black check")

    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(src_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"black found violations:\n{result.stdout}\n{result.stderr}")