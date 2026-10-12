"""
Integration test for Task T005 – curating the reference substructures CSV
and populating its checksum entry.

The test invokes the ``curate_reference_substructures`` script, then
verifies:
  1. The CSV file exists at ``data/raw/reference_substructures_raw.csv``.
  2. ``data/raw/checksums.json`` contains a ``reference_substructures``
     entry whose hash matches the actual SHA‑256 of the CSV.
"""

import hashlib
import json
from pathlib import Path

from llmxive_toolkit import paths

# Import the script’s entry point.  Importing runs the module‑level code
# only; we explicitly call ``main`` to perform the download & checksum.
from code.data.curate_reference_substructures import main as curate_main

def test_curate_reference_substructures():
    # Run the curation script – it will raise on any failure.
    curate_main()

    # Expected locations
    csv_path = paths.data("raw", "reference_substructures_raw.csv")
    checksum_path = paths.data("raw", "checksums.json")

    # 1. CSV must exist
    assert csv_path.is_file(), f"CSV not found at {csv_path}"

    # 2. Manifest must exist and contain the correct entry
    assert checksum_path.is_file(), f"Checksums manifest missing at {checksum_path}"
    with checksum_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "reference_substructures" in manifest, "Missing 'reference_substructures' key in checksums.json"

    entry = manifest["reference_substructures"]
    expected_hash = entry.get("hash")
    assert expected_hash, "Checksum entry missing 'hash' field"

    # Compute the actual hash of the CSV
    sha256 = hashlib.sha256()
    with csv_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual_hash = sha256.hexdigest()

    assert actual_hash == expected_hash, (
        f"Checksum mismatch for reference_substructures_raw.csv: "
        f"expected {expected_hash}, got {actual_hash}"
    )