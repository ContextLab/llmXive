import os
import sys
import pytest
from pathlib import Path
from scripts.create_structure_test import verify_structure

def test_structure_exists(tmp_path):
    """
    Unit test to verify that the create_structure logic creates the expected directories.
    We simulate the structure creation in a temporary path.
    """
    # Create a mock project root in tmp_path
    mock_root = tmp_path / "mock_project"
    mock_root.mkdir()

    # Create the expected directories manually to simulate a successful run
    # (In a real scenario, we'd run create_structure.main() here, but we want to test the verifier)
    required_dirs = [
        "src/ingestion",
        "src/modeling",
        "src/visualization",
        "src/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "docs"
    ]

    for d in required_dirs:
        (mock_root / d).mkdir(parents=True)

    # Verify
    assert verify_structure(mock_root) is True

def test_structure_missing(tmp_path):
    """
    Unit test to verify that the verifier correctly identifies missing directories.
    """
    mock_root = tmp_path / "broken_project"
    mock_root.mkdir()
    # Create only one directory
    (mock_root / "src/ingestion").mkdir(parents=True)

    assert verify_structure(mock_root) is False
