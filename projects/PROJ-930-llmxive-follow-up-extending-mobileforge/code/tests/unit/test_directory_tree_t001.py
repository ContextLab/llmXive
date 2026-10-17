"""Verify that the full directory tree required by T001 exists."""

from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "code/data/raw",
    "code/data/processed",
    "code/data/evaluation",
    "code/models",
    "code/utils",
    "code/tests/unit",
    "code/tests/integration",
    "data",
    "outputs",
]


class TestT001DirectoryTree:
    def test_all_required_directories_exist(self):
        root = paths.root
        missing = [d for d in REQUIRED_DIRS if not (root / d).is_dir()]
        assert not missing, f"Missing directories: {missing}"