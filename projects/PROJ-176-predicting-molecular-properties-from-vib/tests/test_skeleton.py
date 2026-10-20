"""Tests for the T001 project skeleton."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_DIRS = [
    "code",
    "code/data",
    "code/evaluation",
    "code/models",
    "code/utils",
    "tests",
    "data/raw",
    "data/processed",
    "data/external",
    "results",
    "logs",
    "specs/001-predict-molecular-properties",
]

PACKAGE_DIRS = [
    "code",
    "code/data",
    "code/evaluation",
    "code/models",
    "code/utils",
    "tests",
]


def test_expected_directories_exist():
    for rel in EXPECTED_DIRS:
        assert (PROJECT_ROOT / rel).is_dir(), f"missing directory: {rel}"


def test_init_files_are_empty():
    for rel in PACKAGE_DIRS:
        init = PROJECT_ROOT / rel / "__init__.py"
        assert init.is_file(), f"missing __init__.py in {rel}"
        assert init.read_bytes() == b"", f"{init} is not empty"


def test_structure_report_exists_and_complete():
    report = PROJECT_ROOT / "results" / "structure_report.txt"
    assert report.is_file(), "results/structure_report.txt missing"
    listed = set(report.read_text().splitlines())
    for rel in EXPECTED_DIRS:
        assert rel in listed, f"{rel} not listed in structure_report.txt"