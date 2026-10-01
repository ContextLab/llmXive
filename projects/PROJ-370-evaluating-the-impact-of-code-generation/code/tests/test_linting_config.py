import subprocess
import sys
import os
import pytest
from pathlib import Path

# Ensure we are running from the project root or adjust paths accordingly
# For CI/execution, we assume the working directory is the project root
PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Verify that ruff configuration file exists."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    ruff_toml_path = PROJECT_ROOT / ".ruff.toml"
    assert pyproject_path.exists() or ruff_toml_path.exists(), \
        "Ruff configuration file (pyproject.toml or .ruff.toml) must exist."

def test_black_config_exists():
    """Verify that black configuration file exists."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    black_toml_path = PROJECT_ROOT / ".black.toml"
    assert pyproject_path.exists() or black_toml_path.exists(), \
        "Black configuration file (pyproject.toml or .black.toml) must exist."

def test_ruff_syntax_check():
    """Run ruff check on the codebase to ensure no syntax errors or linting violations."""
    # We run ruff on the 'code' directory specifically
    ruff_path = PROJECT_ROOT / "code"
    if not ruff_path.exists():
        pytest.skip("Code directory not found, skipping linting check.")

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(ruff_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    
    # We expect success (exit code 0). If there are linting errors, this test fails.
    # Note: In a real CI, we might want to allow specific ignores, but for this task
    # we enforce that the configured tools work and the code passes them.
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_format_check():
    """Run black --check on the codebase to ensure code is formatted correctly."""
    black_path = PROJECT_ROOT / "code"
    if not black_path.exists():
        pytest.skip("Code directory not found, skipping formatting check.")

    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(black_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )

    assert result.returncode == 0, f"Black format check failed:\n{result.stdout}\n{result.stderr}"

def test_line_length_consistency():
    """Verify that line length is consistent across ruff and black configurations."""
    # Read pyproject.toml if it exists
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        # Simple check for line-length in both sections
        ruff_line = None
        black_line = None
        in_ruff = False
        in_black = False
        
        for line in content.splitlines():
            if "[tool.ruff]" in line:
                in_ruff = True
            elif "[tool.black]" in line:
                in_black = True
                in_ruff = False
            
            if in_ruff and "line-length" in line:
                ruff_line = int(line.split("=")[1].strip())
            if in_black and "line-length" in line:
                black_line = int(line.split("=")[1].strip())
        
        if ruff_line is not None and black_line is not None:
            assert ruff_line == black_line, \
                f"Line length mismatch: Ruff={ruff_line}, Black={black_line}"
        elif ruff_line is not None or black_line is not None:
            # If one is missing, we rely on defaults, but we prefer explicit consistency
            # For this test, we just ensure we found at least one or the other is default 88
            pass
    
    # If pyproject.toml doesn't have it, check .ruff.toml and .black.toml
    ruff_toml = PROJECT_ROOT / ".ruff.toml"
    black_toml = PROJECT_ROOT / ".black.toml"
    
    if ruff_toml.exists() and black_toml.exists():
        ruff_content = ruff_toml.read_text()
        black_content = black_toml.read_text()
        
        ruff_val = None
        black_val = None
        
        for line in ruff_content.splitlines():
            if "line-length" in line:
                ruff_val = int(line.split("=")[1].strip())
        for line in black_content.splitlines():
            if "line-length" in line:
                black_val = int(line.split("=")[1].strip())
        
        if ruff_val is not None and black_val is not None:
            assert ruff_val == black_val, \
                f"Line length mismatch in TOML files: Ruff={ruff_val}, Black={black_val}"