import os
import pytest
from pathlib import Path
from utils.constants import (
    CODE_DIR, DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR,
    DATA_INTERMEDIATE_DIR, TESTS_DIR, STATE_DIR, RESULTS_DIR,
    RESULTS_PLOTS_DIR, CONTRACTS_DIR
)

def test_root_directories_exist():
    """Test that all root directories created by T001a exist."""
    assert CODE_DIR.exists(), f"Directory missing: {CODE_DIR}"
    assert DATA_DIR.exists(), f"Directory missing: {DATA_DIR}"
    assert TESTS_DIR.exists(), f"Directory missing: {TESTS_DIR}"
    assert STATE_DIR.exists(), f"Directory missing: {STATE_DIR}"
    assert RESULTS_DIR.exists(), f"Directory missing: {RESULTS_DIR}"
    assert CONTRACTS_DIR.exists(), f"Directory missing: {CONTRACTS_DIR}"

def test_sub_directories_exist():
    """Test that all sub-directories created by T001b exist."""
    assert DATA_RAW_DIR.exists(), f"Directory missing: {DATA_RAW_DIR}"
    assert DATA_PROCESSED_DIR.exists(), f"Directory missing: {DATA_PROCESSED_DIR}"
    assert DATA_INTERMEDIATE_DIR.exists(), f"Directory missing: {DATA_INTERMEDIATE_DIR}"
    assert RESULTS_PLOTS_DIR.exists(), f"Directory missing: {RESULTS_PLOTS_DIR}"

def test_directories_are_writable():
    """Test that the directories are writable."""
    writable_dirs = [
        CODE_DIR, DATA_DIR, TESTS_DIR, STATE_DIR, RESULTS_DIR, CONTRACTS_DIR,
        DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR, RESULTS_PLOTS_DIR
    ]
    for d in writable_dirs:
        assert os.access(d, os.W_OK), f"Directory is not writable: {d}"
