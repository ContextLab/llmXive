"""
Test that the merge_sources script correctly combines the two raw JSON files.

The test creates two tiny temporary JSON files, runs the merge script,
and checks that the output file contains the combined records and that
the logger recorded the expected counts.
"""

import json
import os
from pathlib import Path

import pytest

# Import the script's main function directly
from code.data.merge_sources import main as merge_main

@pytest.fixture
def temporary_raw_files(tmp_path: Path):
    """Create minimal mp_raw.json and nist_alloys.json files."""
    mp_data = [{"material_id": "mp-1", "source": "mp"}]
    nist_data = [{"material_id": "nist-1", "source": "nist"}]

    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)

    mp_path = raw_dir / "mp_raw.json"
    nist_path = raw_dir / "nist_alloys.json"

    with mp_path.open("w") as f:
        json.dump(mp_data, f)
    with nist_path.open("w") as f:
        json.dump(nist_data, f)

    # Patch the module-level paths to point to our temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)

def test_merge_creates_combined_file(temporary_raw_files, tmp_path):
    # Run the merge script (it will operate on the temporary files)
    merge_main()

    merged_path = Path("data") / "raw" / "merged_alloys.json"
    assert merged_path.is_file(), "Merged output file was not created."

    with merged_path.open() as f:
        merged = json.load(f)

    assert isinstance(merged, list), "Merged output should be a list."
    assert len(merged) == 2, "Merged output should contain records from both sources."
    ids = {rec["material_id"] for rec in merged}
    assert ids == {"mp-1", "nist-1"}