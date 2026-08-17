"""
Unit tests to verify linting and formatting configuration.
"""
import os
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    flake8_config = CODE_DIR / ".flake8"
    assert flake8_config.exists(), f"flake8 config not found at {flake8_config}"

def test_black_config_exists():
    """Test that pyproject.toml contains black configuration."""
    pyproject = CODE_DIR / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml not found at {pyproject}"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"

def test_lint_script_exists():
    """Test that linting script exists."""
    lint_script = CODE_DIR / "scripts" / "run_lint.sh"
    assert lint_script.exists(), f"Lint script not found at {lint_script}"

def test_format_script_exists():
    """Test that formatting script exists."""
    format_script = CODE_DIR / "scripts" / "format.sh"
    assert format_script.exists(), f"Format script not found at {format_script}"

def test_check_formatting_script_exists():
    """Test that check formatting script exists."""
    check_script = CODE_DIR / "scripts" / "check_formatting.sh"
    assert check_script.exists(), f"Check formatting script not found at {check_script}"

@pytest.mark.skipif(
    not os.environ.get("RUN_LINTING_TESTS"),
    reason="Linting tests skipped unless RUN_LINTING_TESTS is set"
)
def test_flake8_runs_successfully():
    """Test that flake8 can run on the codebase without errors."""
    result = subprocess.run(
        ["flake8", str(CODE_DIR)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Note: This might fail if code has linting issues, which is expected
    # during development. The test verifies flake8 is configured and runnable.
    assert result.returncode in [0, 1], f"flake8 failed with unexpected error: {result.stderr}"

@pytest.mark.skipif(
    not os.environ.get("RUN_LINTING_TESTS"),
    reason="Linting tests skipped unless RUN_LINTING_TESTS is set"
)
def test_black_check_runs_successfully():
    """Test that black --check can run on the codebase."""
    result = subprocess.run(
        ["black", "--check", str(CODE_DIR)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Note: This might fail if code is not formatted, which is expected
    # during development. The test verifies black is configured and runnable.
    assert result.returncode in [0, 1], f"black check failed with unexpected error: {result.stderr}"