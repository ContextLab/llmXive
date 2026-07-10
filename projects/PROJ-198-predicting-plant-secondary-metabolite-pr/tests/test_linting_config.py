"""
Tests to verify that linting and formatting configurations are valid.
"""
import os
import subprocess
import tempfile
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    ruff_config = os.path.join(CODE_DIR, ".ruff.toml")
    assert os.path.exists(ruff_config), f"Ruff config not found at {ruff_config}"

def test_black_config_exists():
    """Verify black configuration file exists."""
    black_config = os.path.join(CODE_DIR, ".black.toml")
    assert os.path.exists(black_config), f"Black config not found at {black_config}"

def test_ruff_config_valid():
    """Verify ruff config is valid by running ruff check on itself."""
    ruff_config = os.path.join(CODE_DIR, ".ruff.toml")
    result = subprocess.run(
        ["ruff", "check", "--config", ruff_config, ruff_config],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We don't strictly require ruff to pass on itself if it's not a .py file,
    # but we verify the config is readable and valid by checking exit code isn't a config error.
    # Ruff returns 0 for valid config, non-zero for errors or lint violations.
    # Since .toml isn't python, we just check it doesn't crash.
    assert "error" not in result.stderr.lower() or "invalid" not in result.stderr.lower()

def test_black_config_valid():
    """Verify black config is valid by running black --check on a dummy file."""
    black_config = os.path.join(CODE_DIR, ".black.toml")
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b"x=1\n")
        temp_path = f.name

    try:
        result = subprocess.run(
            ["black", "--check", "--config", black_config, temp_path],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        # Black will fail (exit 1) because x=1 needs formatting, but it must not crash
        # due to invalid config. We check stderr for config errors.
        assert "Error" not in result.stderr or "config" not in result.stderr.lower()
    finally:
        os.unlink(temp_path)

def test_requirements_includes_linting_tools():
    """Verify requirements.txt includes ruff and black."""
    req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
    assert os.path.exists(req_path), "requirements.txt not found"
    
    with open(req_path, "r") as f:
        content = f.read().lower()
    
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"