"""Integration test for T004: data directory structure and .gitkeep files."""

import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

REQUIRED_DIRS = [
    os.path.join("data", "raw"),
    os.path.join("data", "generated"),
    os.path.join("data", "results"),
]


def test_data_directories_exist():
    for d in REQUIRED_DIRS:
        full = os.path.join(PROJECT_ROOT, d)
        assert os.path.isdir(full), f"Missing directory: {full}"


def test_gitkeep_files_exist():
    for d in REQUIRED_DIRS:
        full = os.path.join(PROJECT_ROOT, d, ".gitkeep")
        assert os.path.isfile(full), f"Missing .gitkeep: {full}"