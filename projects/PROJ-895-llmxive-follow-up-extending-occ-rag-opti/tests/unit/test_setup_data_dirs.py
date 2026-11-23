"""
Unit test for the ``code/scripts/setup_data_dirs.py`` utility.
It verifies that running the script creates the expected directory
hierarchy and an empty ``checksums.json`` file.
"""

import json
import os
import shutil
from pathlib import Path

import pytest

# Import the functions from the script using its module path.
# The script adds no package-level __init__, so we import via importlib.
import importlib.util

SCRIPT_PATH = Path(__file__).parents[2] / "code" / "scripts" / "setup_data_dirs.py"

spec = importlib.util.spec_from_file_location("setup_data_dirs", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None
spec.loader.exec_module(module)  # type: ignore


@pytest.fixture(scope="function")
def clean_workspace(tmp_path):
    """
    Create a temporary workspace that mimics the project root.
    The fixture changes the working directory to the temporary path,
    runs the script, and then yields control back to the test.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Ensure no leftover data directory exists before the test.
        if (tmp_path / "data").exists():
            shutil.rmtree(tmp_path / "data")
        yield tmp_path
    finally:
        os.chdir(original_cwd)


def test_directories_and_checksums_created(clean_workspace):
    """
    After invoking ``module.main()``, the following must exist:
      - data/
      - data/raw/
      - data/processed/
      - data/checksums.json (valid empty JSON)
    """
    # Run the script's main function.
    module.main()

    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    checksums_file = data_dir / "checksums.json"

    assert data_dir.is_dir(), "data/ directory was not created"
    assert raw_dir.is_dir(), "data/raw/ directory was not created"
    assert processed_dir.is_dir(), "data/processed/ directory was not created"
    assert checksums_file.is_file(), "data/checksums.json was not created"

    # The checksums file should contain valid JSON (empty dict is acceptable)
    with checksums_file.open("r", encoding="utf-8") as f:
        content = json.load(f)
    assert isinstance(content, dict), "checksums.json does not contain a JSON object"
    assert len(content) == 0, "checksums.json should be empty after initialisation"

# The test suite can be executed via ``pytest tests/unit``.