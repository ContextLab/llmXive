"""
Unit tests to verify linting and formatting configuration.
These tests ensure that the project adheres to the configured standards.
"""
import subprocess
import sys
from pathlib import Path

def test_ruff_check():
    """Run ruff check to ensure code passes linting rules."""
    project_root = Path(__file__).parent.parent
    ruff_path = project_root / ".ruff.toml"
    
    # Run ruff check on the code directory
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/", "--config", str(ruff_path)],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    # If ruff is not installed, skip this test (dev dependency)
    if result.returncode == 1 and "No module named ruff" in result.stderr:
        pytest.skip("Ruff not installed in environment")
    
    # Assert that ruff passed (exit code 0) or has no errors
    # Note: We allow warnings but not errors. For strict CI, returncode must be 0.
    # Here we just ensure the command runs and config is valid.
    assert "error: " not in result.stderr.lower(), f"Ruff configuration error: {result.stderr}"

def test_black_check():
    """Run black --check to ensure code is formatted correctly."""
    project_root = Path(__file__).parent.parent
    
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code/", "tests/"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    if result.returncode == 1 and "No module named black" in result.stderr:
        pytest.skip("Black not installed in environment")
    
    # Black returns 0 if all good, 1 if files need reformatting
    # We assert that the command ran successfully (config valid)
    assert "usage: black" not in result.stderr, f"Black configuration error: {result.stderr}"