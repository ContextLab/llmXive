"""
Simple test to ensure that the project skeleton was created correctly.
It checks that the expected directories exist and that the structure report
file contains the list of those directories.
"""
import os
from pathlib import Path

import pytest

# Expected directories relative to the project root
EXPECTED_DIRS = [
    "code",
    "code/data",
    "code/models",
    "code/evaluation",
    "code/utils",
    "tests",
    "data/raw",
    "data/processed",
    "data/external",
    "results",
    "logs",
    "specs/001-predict-molecular-properties",
    "specs/001-predict-molecular-properties/contracts",
]

def test_directories_exist():
    for d in EXPECTED_DIRS:
        assert Path(d).is_dir(), f"Directory {d} should exist"

def test_structure_report():
    report_path = Path("results") / "structure_report.txt"
    assert report_path.is_file(), "Structure report file should exist"
    with report_path.open() as f:
        lines = [line.strip() for line in f.readlines()]
    # The report should contain at least all expected directories
    for d in EXPECTED_DIRS:
        assert d in lines, f"{d} missing from structure report"

# Run the test only if this file is executed directly (optional)
if __name__ == "__main__":
    pytest.main([__file__])