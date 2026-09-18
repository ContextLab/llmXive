"""
Unit tests for T001b: Directory creation verification.
"""
import os
import pytest
from pathlib import Path
import sys

# Add project root to path to import setup logic if needed, 
# though here we verify filesystem state directly.
# The script code/setup_dirs.py is executed to create the dirs.

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
TESTS_UNIT = TESTS_DIR / "unit"
TESTS_INTEGRATION = TESTS_DIR / "integration"
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_REPORTS = DOCS_DIR / "reports"

def test_data_raw_exists():
    """Verify data/raw/ directory exists (T001b)."""
    assert DATA_RAW.exists(), f"Directory {DATA_RAW} does not exist."
    assert DATA_RAW.is_dir(), f"{DATA_RAW} is not a directory."

def test_data_processed_exists():
    """Verify data/processed/ directory exists (T001b)."""
    assert DATA_PROCESSED.exists(), f"Directory {DATA_PROCESSED} does not exist."
    assert DATA_PROCESSED.is_dir(), f"{DATA_PROCESSED} is not a directory."

def test_code_dir_exists():
    """Verify code/ directory exists (T001a)."""
    assert CODE_DIR.exists(), f"Directory {CODE_DIR} does not exist."

def test_tests_unit_exists():
    """Verify tests/unit/ directory exists (T001a)."""
    assert TESTS_UNIT.exists(), f"Directory {TESTS_UNIT} does not exist."

def test_tests_integration_exists():
    """Verify tests/integration/ directory exists (T001a)."""
    assert TESTS_INTEGRATION.exists(), f"Directory {TESTS_INTEGRATION} does not exist."

def test_docs_reports_exists():
    """Verify docs/reports/ directory exists (T001c)."""
    assert DOCS_REPORTS.exists(), f"Directory {DOCS_REPORTS} does not exist."