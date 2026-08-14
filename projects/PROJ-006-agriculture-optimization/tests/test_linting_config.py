"""
Test suite for T003: Linting and Formatting Configuration.
Verifies that black, flake8, isort are installed and configured,
and that the codebase adheres to these standards.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest

def get_project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).resolve().parent.parent

def run_command(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Helper to run a shell command and return the result."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )

@pytest.fixture(scope="module")
def project_root() -> Path:
    return get_project_root()

def test_black_is_installed(project_root: Path):
    """Verify black is available in the environment."""
    result = run_command([sys.executable, "-m", "black", "--version"], cwd=project_root)
    assert result.returncode == 0, f"Black not found: {result.stderr}"
    assert "black" in result.stdout.lower()

def test_flake8_is_installed(project_root: Path):
    """Verify flake8 is available in the environment."""
    result = run_command([sys.executable, "-m", "flake8", "--version"], cwd=project_root)
    assert result.returncode == 0, f"Flake8 not found: {result.stderr}"

def test_isort_is_installed(project_root: Path):
    """Verify isort is available in the environment."""
    result = run_command([sys.executable, "-m", "isort", "--version"], cwd=project_root)
    assert result.returncode == 0, f"Isort not found: {result.stderr}"

def test_gitignore_exists(project_root: Path):
    """Verify .gitignore exists at project root."""
    assert (project_root / ".gitignore").exists(), ".gitignore missing"

def test_setup_cfg_exists(project_root: Path):
    """Verify setup.cfg exists for legacy config support."""
    assert (project_root / "setup.cfg").exists(), "setup.cfg missing"

def test_pyproject_toml_exists(project_root: Path):
    """Verify pyproject.toml exists for modern config support."""
    assert (project_root / "pyproject.toml").exists(), "pyproject.toml missing"

def test_requirements_txt_includes_dev_tools(project_root: Path):
    """Verify requirements.txt includes dev tools."""
    req_file = project_root / "requirements.txt"
    assert req_file.exists(), "requirements.txt missing"
    content = req_file.read_text()
    assert "black" in content, "black missing from requirements.txt"
    assert "flake8" in content, "flake8 missing from requirements.txt"
    assert "isort" in content, "isort missing from requirements.txt"

def test_code_passes_flake8(project_root: Path):
    """Verify code passes flake8 checks."""
    # Exclude data, venv, build dirs
    result = run_command(
        [sys.executable, "-m", "flake8", "src", "scripts", "tests"],
        cwd=project_root
    )
    assert result.returncode == 0, f"Flake8 errors found:\n{result.stdout}\n{result.stderr}"

def test_code_passes_isort(project_root: Path):
    """Verify code passes isort checks (diff mode)."""
    result = run_command(
        [sys.executable, "-m", "isort", "--check-only", "src", "scripts", "tests"],
        cwd=project_root
    )
    assert result.returncode == 0, f"Isort errors found:\n{result.stdout}\n{result.stderr}"

def test_code_passes_black(project_root: Path):
    """Verify code passes black checks (diff mode)."""
    result = run_command(
        [sys.executable, "-m", "black", "--check", "src", "scripts", "tests"],
        cwd=project_root
    )
    assert result.returncode == 0, f"Black errors found:\n{result.stdout}\n{result.stderr}"