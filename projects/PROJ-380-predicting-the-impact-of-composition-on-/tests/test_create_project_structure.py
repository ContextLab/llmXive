"""
Test that the top‑level project directories required by T001 exist.
The script `code/create_project_structure.py` should have created them
before the test suite runs.
"""

import pytest
from pathlib import Path
from llmxive_toolkit import paths

@pytest.mark.parametrize(
    "directory_name",
    ["code", "data", "tests", "docs", "artifacts"]
)
def test_directory_exists(directory_name: str):
    """
    Verify that each required top‑level directory exists and is a folder.
    """
    dir_path: Path = paths.root / directory_name
    assert dir_path.is_dir(), f"Directory {directory_name} was not created"