"""
Tests to verify that linting (ruff) and formatting (black) are correctly configured.
These tests ensure the project enforces code quality standards.
"""
import subprocess
import sys
import os
import tempfile
import shutil

def run_command(cmd, cwd=None):
    """Helper to run a shell command and return stdout, stderr, and return code."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr, result.returncode

def test_ruff_config_exists():
    """Verify that .ruff.toml exists in the code directory."""
    # The config is expected at code/.ruff.toml based on task requirements
    config_path = os.path.join("code", ".ruff.toml")
    assert os.path.exists(config_path), f"Ruff config not found at {config_path}"

def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml."""
    config_path = os.path.join("pyproject.toml")
    assert os.path.exists(config_path), f"Black config not found at {config_path}"
    with open(config_path, "r") as f:
        content = f.read()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"

def test_ruff_check_code():
    """Run ruff check on the code directory to ensure no violations exist."""
    # Ensure ruff is installed
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pytest.skip("Ruff installation failed")

    # Run ruff check
    cmd = "ruff check code/"
    stdout, stderr, returncode = run_command(cmd)

    # If returncode is 0, checks passed. If non-zero, we check if it's just a config issue or code issue.
    # For this test, we expect the code to pass the configured rules.
    if returncode != 0:
        print(f"Ruff check failed:\n{stdout}\n{stderr}")
        # Fail the test if there are linting errors
        assert False, f"Ruff found linting errors. Output: {stdout}"

def test_black_check_code():
    """Run black --check on the code directory to ensure formatting is correct."""
    # Ensure black is installed
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "black"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pytest.skip("Black installation failed")

    cmd = "black --check code/"
    stdout, stderr, returncode = run_command(cmd)

    if returncode != 0:
        print(f"Black check failed:\n{stdout}\n{stderr}")
        assert False, f"Black found formatting errors. Output: {stdout}"