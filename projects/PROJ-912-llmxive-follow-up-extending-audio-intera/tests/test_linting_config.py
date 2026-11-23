import subprocess
import sys
import os
from pathlib import Path
import pytest

def test_ruff_config_exists():
    """Verify ruff configuration file exists in code/."""
    code_dir = Path(__file__).parent.parent / "code"
    assert (code_dir / "ruff.toml").exists(), "ruff.toml missing in code/"
    assert (code_dir / ".ruff.toml").exists(), ".ruff.toml missing in code/"

def test_black_config_exists():
    """Verify Black configuration exists in pyproject.toml."""
    code_dir = Path(__file__).parent.parent / "code"
    pyproject = code_dir / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml missing in code/"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"

def test_ruff_can_check_code():
    """Verify ruff can successfully run against the codebase."""
    code_dir = Path(__file__).parent.parent / "code"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect 0 (success) or 1 (linting errors found), but not 2 (config error)
        assert result.returncode in [0, 1], f"Ruff failed to run: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")

def test_black_can_check_code():
    """Verify black can successfully run against the codebase."""
    code_dir = Path(__file__).parent.parent / "code"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect 0 (success) or 1 (would reformat), but not 2 (config error)
        assert result.returncode in [0, 1], f"Black failed to run: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")

def test_ruff_config_syntax_valid():
    """Verify ruff configuration syntax is valid."""
    code_dir = Path(__file__).parent.parent / "code"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--config", str(code_dir / "ruff.toml"), "--isolated"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # If config is invalid, ruff usually returns 2
        assert result.returncode != 2, f"Ruff config syntax error: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed")

def test_pyproject_black_section_syntax():
    """Verify pyproject.toml Black section is valid."""
    code_dir = Path(__file__).parent.parent / "code"
    pyproject = code_dir / "pyproject.toml"
    
    # Basic validation: check for required keys
    content = pyproject.read_text()
    assert "line-length" in content, "Black line-length missing"
    assert "target-version" in content, "Black target-version missing"