"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from config import (
    RANDOM_SEED,
    MAX_ITERATIONS,
    ALTERNATIVE_ITERATIONS,
    TIMEOUT_HOURS,
    MAX_RUNTIME_SECONDS,
    DATA_PROCESSED_DIR,
    ensure_config_dirs,
    ALPHA_THRESHOLD
)

def test_random_seed():
    assert RANDOM_SEED == 42

def test_max_iterations():
    assert MAX_ITERATIONS == 1000

def test_alternative_iterations():
    assert ALTERNATIVE_ITERATIONS == 1000

def test_timeout_hours():
    assert TIMEOUT_HOURS == 6

def test_max_runtime_seconds():
    assert MAX_RUNTIME_SECONDS == TIMEOUT_HOURS * 3600

def test_path_types():
    assert isinstance(DATA_PROCESSED_DIR, Path)

def test_ensure_config_dirs():
    # This function should run without error
    ensure_config_dirs()
    assert DATA_PROCESSED_DIR.exists()

def test_alpha_threshold():
    assert ALPHA_THRESHOLD == 0.05