import os
import sys
from pathlib import Path
import pytest

# Add code to path if running from tests
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from config import DATA_RAW, DATA_CURATED, DATA_RESULTS, TESTS_DIR, CONTRACTS_DIR

def test_directories_exist():
    """Verify that the required project directories exist."""
    required_dirs = [
        DATA_RAW,
        DATA_CURATED,
        DATA_RESULTS,
        TESTS_DIR,
        CONTRACTS_DIR
    ]
    for d in required_dirs:
        assert d.exists(), f"Directory {d} does not exist."
        assert d.is_dir(), f"{d} is not a directory."

def test_config_imports():
    """Verify config.py is importable and has expected constants."""
    from config import HARD_INSTANCE_PERCENTILE, COVERAGE_COLUMN_NAME
    assert isinstance(HARD_INSTANCE_PERCENTILE, (int, float))
    assert isinstance(COVERAGE_COLUMN_NAME, str)
    assert COVERAGE_COLUMN_NAME != ""
