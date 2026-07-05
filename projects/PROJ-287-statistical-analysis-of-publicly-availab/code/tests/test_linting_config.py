"""
Tests to verify that linting and formatting configuration files exist and are valid.
"""
import subprocess
import os
from pathlib import Path

def test_ruff_config_valid():
    """Verify .ruff.toml exists and ruff can parse it."""
    repo_root = Path(__file__).parent.parent
    config_path = repo_root / ".ruff.toml"
    
    assert config_path.exists(), "Configuration file .ruff.toml does not exist"
    
    # Run ruff check to ensure config is valid
    result = subprocess.run(
        ["ruff", "check", "--config", str(config_path), "--no-cache", "."],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    
    # We expect it to run without crashing (exit code 0 or 1 for linting issues is fine)
    # Exit code 2 usually means config error
    assert result.returncode != 2, f"Ruff config error: {result.stderr}"

def test_black_config_valid():
    """Verify pyproject.toml contains black config and black can parse it."""
    repo_root = Path(__file__).parent.parent
    config_path = repo_root / "pyproject.toml"
    
    assert config_path.exists(), "Configuration file pyproject.toml does not exist"
    
    # Run black --check to ensure config is valid
    # We only check a small subset to avoid long runtime in tests
    result = subprocess.run(
        ["black", "--check", "--config", str(config_path), "--diff", "tests/test_linting_config.py"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    
    # Exit code 0 = formatted correctly
    # Exit code 1 = would reformat (valid config, just not formatted)
    # Exit code 2 = config error or syntax error
    assert result.returncode != 2, f"Black config error: {result.stderr}"