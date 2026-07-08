"""
Unit test for the `create_raw_dir` utility.

It verifies that:
* The `data/raw` directory is created under a temporary project root.
* A placeholder CSV file with the correct header is generated.
"""

import importlib
import types
from pathlib import Path

import pytest

# Import the module under test
from create_raw_dir import ensure_raw_dir


def test_ensure_raw_dir_creates_directory_and_placeholder(tmp_path, monkeypatch):
    """
    Run `ensure_raw_dir` with a temporary project root and confirm that
    the expected directory and placeholder CSV are created.
    """
    # Patch the project root function to point to the temporary directory
    import utils.config
    monkeypatch.setattr(utils.config, "get_project_root", lambda: tmp_path)

    # Execute the function
    raw_dir = ensure_raw_dir()

    # Expected path
    expected_dir = tmp_path / "data" / "raw"
    assert raw_dir == expected_dir
    assert raw_dir.is_dir(), "The raw data directory should exist"

    placeholder = raw_dir / "dataset_placeholder.csv"
    assert placeholder.is_file(), "Placeholder CSV should be created"
    # Verify the header line matches the specification
    expected_header = "smiles,solvent,diffusion_coefficient"
    actual_header = placeholder.read_text().strip()
    assert actual_header == expected_header, "Placeholder CSV header is incorrect"