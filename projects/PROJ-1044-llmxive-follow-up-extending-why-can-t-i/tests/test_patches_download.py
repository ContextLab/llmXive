"""Test that the patches download script creates the expected artifacts."""

import csv
from pathlib import Path

import pytest

from src.data.patches_download import main as patches_main

@pytest.mark.parametrize("temp_dir", [None])
def test_patches_created():
    """Run the script and verify patches and manifest are consistent."""
    # Execute the script; it should return 0 on success.
    assert patches_main() == 0

    patches_dir = Path("data/patches")
    manifest_path = patches_dir / "manifest.csv"

    # Ensure the directory exists and contains at least 20 PNG files.
    patch_files = sorted(patches_dir.glob("*.png"))
    assert len(patch_files) >= 20, f"Found {len(patch_files)} patch files"

    # Verify the manifest exists and has a matching number of rows.
    assert manifest_path.is_file(), "manifest.csv missing"
    with manifest_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == len(patch_files), (
        f"Manifest row count ({len(rows)}) does not match file count ({len(patch_files)})"
    )

    # Check that each row refers to an existing file and contains required fields.
    required_fields = {"filename", "source_url", "class_label"}
    for row in rows:
        assert required_fields.issubset(row.keys()), "Missing columns in manifest"
        file_path = patches_dir / row["filename"]
        assert file_path.is_file(), f"Patch file missing: {file_path}"
