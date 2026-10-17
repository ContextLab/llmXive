"""T001 verification tests: project directory hierarchy and tree audit files."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DIRS = [
    "code/ingestion",
    "code/processing",
    "code/analysis",
    "code/utils",
    "code/tests",
    "data/raw/tng100",
    "data/raw/millennium",
    "data/processed",
    "outputs/figures",
    "outputs/reports",
]

REQUIRED_FILES = [
    "docs/quickstart.md",
    "docs/README.md",
    "data_dir_tree.txt",
    "output_dir_tree.txt",
]


def test_required_directories_exist():
    missing = [d for d in REQUIRED_DIRS if not (PROJECT_ROOT / d).is_dir()]
    assert not missing, f"Missing directories: {missing}"


def test_required_files_exist():
    missing = [f for f in REQUIRED_FILES if not (PROJECT_ROOT / f).is_file()]
    assert not missing, f"Missing files: {missing}"


def test_data_tree_lists_hierarchy():
    content = (PROJECT_ROOT / "data_dir_tree.txt").read_text()
    for name in ["raw/", "tng100/", "millennium/", "processed/"]:
        assert name in content, f"{name} missing from data_dir_tree.txt"


def test_output_tree_lists_hierarchy():
    content = (PROJECT_ROOT / "output_dir_tree.txt").read_text()
    for name in ["outputs/", "figures/", "reports/", "docs/", "code/"]:
        assert name in content, f"{name} missing from output_dir_tree.txt"