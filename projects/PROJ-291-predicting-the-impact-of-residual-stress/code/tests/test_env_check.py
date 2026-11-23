"""
Test suite for the environment‑check script (task T001).

The test verifies:
1. The script can be executed as a module (``python -m code.src.env_check``) and exits with status 0.
2. The global configuration module defines ``SEED``.
"""

import subprocess
import sys
import pytest

def test_env_check_exits_successfully():
    """Run the env_check module and ensure it exits with code 0."""
    # We use 'code.src.env_check' to match the project's artifact path.
    result = subprocess.run(
        [sys.executable, "-m", "code.src.env_check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"env_check failed with return code {result.returncode}. stderr: {result.stderr}"

def test_config_defines_seed():
    """The configuration module must expose a reproducible SEED."""
    from code.src import config

    assert hasattr(config, "SEED"), "config.SEED is missing"
    # The seed should be an int for reproducibility.
    assert isinstance(config.SEED, int)
    assert config.SEED == 42