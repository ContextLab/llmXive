"""
Unit test for the configuration loader.
"""

import sys
from pathlib import Path

# Ensure the project code package is on the import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from config import load_config
from exceptions import InvalidPrimeError

def test_load_config_defaults():
    """
    Load the configuration without any CLI overrides and compare the
    values against the contents of code/config.yaml.
    """
    expected = {
        "N": 1234,
        "primes": [3, 5, 7, 11],
        "seed": 12345,
        "memory_limit_mb": 6000,
        "memory_check_interval": 5000,
    }

    cfg = load_config()
    for key, val in expected.items():
        assert key in cfg, f"Missing key '{key}' in loaded config"
        assert cfg[key] == val, f"Config value for '{key}' does not match: expected {val}, got {cfg[key]}"

def test_invalid_prime_raises_error():
    """Verify that unsupported primes trigger InvalidPrimeError."""
    import argparse
    
    # Mock CLI args with an unsupported prime
    args = argparse.Namespace(primes="13", N=100, seed=42, memory_limit_mb=6000, memory_check_interval=10000)
    
    with pytest.raises(InvalidPrimeError) as excinfo:
        load_config(cli_args=args)
    
    assert "Invalid prime modulus 13" in str(excinfo.value)

# Import pytest for the test above
import pytest
