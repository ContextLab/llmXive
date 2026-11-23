"""
Integration test to verify that the required top‑level project directories exist.
"""

import pytest
from pathlib import Path
from llmxive_toolkit import paths


def test_project_structure():
    """
    Ensure that the four mandatory directories are present at the repository root:
    src/, tests/, data/, and results/.
    """
    root = paths.root
    required_dirs = ["src", "tests", "data", "results"]
    for dirname in required_dirs:
        dir_path = root / dirname
        assert dir_path.is_dir(), f"Required directory missing: {dir_path}"