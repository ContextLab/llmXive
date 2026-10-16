"""Scaffolding tests (T001e): verify the project directory layout exists.

These tests confirm the Phase 0 scaffolding tasks (T001a-T001e) are in
place: code/, data/raw/, data/processed/, data/results/, and tests/.
"""

from pathlib import Path

# Project root is the parent of the tests/ directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_project_root_exists():
    assert PROJECT_ROOT.is_dir()


def test_code_directory_exists():
    code_dir = PROJECT_ROOT / "code"
    assert code_dir.is_dir(), "code/ directory must exist (T001a)"
    assert any(code_dir.iterdir()), "code/ directory should not be empty"


def test_data_raw_directory_exists():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    assert raw_dir.is_dir(), "data/raw/ directory must exist (T001b)"


def test_data_processed_directory_exists():
    processed_dir = PROJECT_ROOT / "data" / "processed"
    assert processed_dir.is_dir(), "data/processed/ directory must exist (T001c)"


def test_data_results_directory_exists():
    results_dir = PROJECT_ROOT / "data" / "results"
    assert results_dir.is_dir(), "data/results/ directory must exist (T001d)"


def test_tests_directory_exists():
    tests_dir = PROJECT_ROOT / "tests"
    assert tests_dir.is_dir(), "tests/ directory must exist (T001e)"
    assert (tests_dir / "test_project_structure.py").is_file()