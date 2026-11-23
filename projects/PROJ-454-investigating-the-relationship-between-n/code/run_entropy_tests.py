"""Run the T005/T011 entropy unit tests and report the outcome.

Exits non-zero if any test fails, so CI can gate on this script.
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_PATH = PROJECT_ROOT / "tests" / "unit" / "test_entropy.py"

if __name__ == "__main__":
    sys.exit(pytest.main([str(TEST_PATH), "-v"]))