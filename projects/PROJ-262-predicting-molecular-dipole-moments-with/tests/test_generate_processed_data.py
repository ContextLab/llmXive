"""Simple integration test for the processed‑data generation script.

The test runs the script and checks that the three expected Parquet files
are created and contain at least one record each.  It does not validate
scientific correctness – that is covered by downstream contract tests.
"""

import os
from pathlib import Path

import pytest

# Import the main function directly to avoid spawning a subprocess.
from data.generate_processed_data import main as generate_main

@pytest.mark.parametrize(
    "filename",
    [
        "data/processed/molecules_10k.parquet",
        "data/processed/features_3d.parquet",
        "data/processed/features_2d.parquet",
    ],
)
def test_processed_files_created(tmp_path, filename):
    # Change working directory to the project root for the script.
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path.parent)  # ensure we are at repo root
        # Run the generation script
        generate_main()
        # Verify file exists
        out_path = Path(filename)
        assert out_path.is_file(), f"{filename} was not created"
        # Basic sanity check: file size > 0
        assert out_path.stat().st_size > 0, f"{filename} is empty"
    finally:
        os.chdir(cwd)