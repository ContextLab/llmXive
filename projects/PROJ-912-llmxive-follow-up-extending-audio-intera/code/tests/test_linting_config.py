import subprocess
import sys
import os
from pathlib import Path
import pytest

def test_ruff_config_exists():
    """Verify that ruff configuration exists in the project."""
    code_root = Path(__file__).resolve().parent.parent
    ruff_toml = code_root / "ruff.toml"
    pyproject = code_root / "pyproject.toml"
    
    assert ruff_toml.exists() or pyproject.exists(), "Ruff configuration file (ruff.toml or pyproject.toml) must exist"

def test_black_config_exists():
    """Verify that black configuration exists in the project."""
    code_root = Path(__file__).resolve().parent.parent
    pyproject = code_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml must exist for Black configuration"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section [tool.black] must exist in pyproject.toml"

def test_ruff_can_check_code():
    """Verify that ruff can successfully run a check on the codebase."""
    code_root = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_root)],
            capture_output=True,
            text=True,
            timeout=60
        )
        # Ruff returns 0 if no errors, 1 if errors found. Both are valid runs.
        # We just want to ensure it executed without crashing.
        assert result.returncode in (0, 1), f"Ruff check failed with unexpected return code {result.returncode}: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")

def test_black_can_check_code():
    """Verify that black can successfully run a check on the codebase."""
    code_root = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(code_root)],
            capture_output=True,
            text=True,
            timeout=60
        )
        # Black returns 0 if formatted correctly, 1 if reformatting needed.
        assert result.returncode in (0, 1), f"Black check failed with unexpected return code {result.returncode}: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")

def test_ruff_config_syntax_valid():
    """Verify that the ruff configuration file is syntactically valid."""
    code_root = Path(__file__).resolve().parent.parent
    ruff_toml = code_root / "ruff.toml"
    
    if ruff_toml.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "config", "show", str(ruff_toml)],
                capture_output=True,
                text=True,
                timeout=30
            )
            # If ruff can show the config, it's valid
            assert result.returncode == 0, f"Ruff config is invalid: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("Ruff not installed")

def test_pyproject_black_section_syntax():
    """Verify that the Black section in pyproject.toml is valid."""
    code_root = Path(__file__).resolve().parent.parent
    pyproject = code_root / "pyproject.toml"
    
    if pyproject.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--config", str(pyproject), "--check", "--diff", "--quiet", str(code_root)],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Black returning 0 or 1 (needs format) means the config was parsed successfully
            assert result.returncode in (0, 1), f"Black config syntax error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("Black not installed")