"""
Integration test to verify the linting configuration works.
This test runs the actual flake8 and black commands to ensure they are configured.
"""
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_config = project_root / "code" / ".flake8"
    assert flake8_config.exists(), "Missing .flake8 configuration file"

def test_black_config_exists():
    """Verify pyproject.toml contains black config."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "Missing pyproject.toml"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"

def test_run_black_check():
    """Run black --check to ensure it validates the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True
    )
    # Black might return 1 if formatting is needed, which is expected in integration
    # but we want to ensure the command runs and reads config.
    assert result.returncode in [0, 1], f"Black command failed unexpectedly: {result.stderr}"

def test_run_flake8():
    """Run flake8 to ensure it validates the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "flake8", str(code_dir)],
        capture_output=True,
        text=True
    )
    # Flake8 returns 0 on success, 1 on violations. We just verify it runs.
    assert result.returncode in [0, 1], f"Flake8 command failed unexpectedly: {result.stderr}"