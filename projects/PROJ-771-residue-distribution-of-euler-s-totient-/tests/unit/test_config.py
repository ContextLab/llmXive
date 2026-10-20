"""
Unit test for the configuration loader.

This test verifies that the ``load_config`` function correctly reads the
default ``code/config.yaml`` file and returns a dictionary with the
expected values for ``N``, ``primes``, ``seed`` and ``memory_limit_mb``.
"""

import sys
import json
from pathlib import Path

# Ensure the project ``code`` package is on the import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from config import load_config

def test_load_config_defaults():
    """
    Load the configuration without any CLI overrides and compare the
    values against the contents of ``code/config.yaml``.
    """
    # The YAML file contains the following values (kept in sync with the
    # file in the repository):
    expected = {
        "N": 1234,
        "primes": [3, 5, 7, 11],
        "seed": 2021,
        "memory_limit_mb": 6000,
        "memory_check_interval": 5000,
    }

    cfg = load_config()  # No CLI args → pure YAML loader
    # The loader returns a plain ``dict``; we compare the relevant keys.
    for key, val in expected.items():
        assert key in cfg, f"Missing key '{key}' in loaded config"
        assert cfg[key] == val, f"Config value for '{key}' does not match: expected {val}, got {cfg[key]}"