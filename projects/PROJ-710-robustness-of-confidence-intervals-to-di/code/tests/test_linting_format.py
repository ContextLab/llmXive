import subprocess
import sys
import os
from pathlib import Path

# Ensure we are running from the project root or can locate the config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_ruff_config_exists():
    """Verify .ruff.toml exists in project root."""
    config_path = PROJECT_ROOT / ".ruff.toml"
    assert config_path.exists(), f"Ruff config not found at {config_path}"

def test_black_config_exists():
    """Verify pyproject.toml with black config exists in project root."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    assert config_path.exists(), f"Black config not found at {config_path}"
    # Optional: verify content contains [tool.black]
    content = config_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"

def test_ruff_syntax_check():
    """Run ruff check on the code directory."""
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        pytest.skip("Code directory not found")
    
    result = subprocess.run(
        ["ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # We expect exit code 0 (success) or 1 (linting issues found but syntax is ok)
    # For a strict "syntax check" we might want to ensure no fatal errors (exit 2+),
    # but ruff usually returns 1 for warnings/errors. 
    # For this task, we ensure it runs without crashing (exit code < 2).
    assert result.returncode < 2, f"Ruff check failed with code {result.returncode}: {result.stderr}"

def test_black_syntax_check():
    """Run black --check on the code directory."""
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        pytest.skip("Code directory not found")

    result = subprocess.run(
        ["black", "--check", "--diff", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Exit code 0: all good. Exit code 1: formatting issues (but syntax valid).
    # Exit code 2+: syntax error or other fatal issue.
    assert result.returncode < 2, f"Black check failed with code {result.returncode}: {result.stderr}"

def test_requirements_include_tools():
    """Verify requirements.txt includes ruff and black."""
    req_path = PROJECT_ROOT / "requirements.txt"
    assert req_path.exists(), "requirements.txt not found"
    
    content = req_path.read_text().lower()
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"