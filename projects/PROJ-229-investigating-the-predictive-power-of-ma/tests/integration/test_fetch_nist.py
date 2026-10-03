"""
Integration test for T005b – fetch_nist_data.

The test runs the ``fetch_nist_data`` script and asserts that:
  * The output file ``data/raw/nist_data.json`` exists.
  * The file contains at least 500 records.
  * The accompanying checksum file matches the data.
"""

import json
from pathlib import Path

import pytest

# The script under test provides a ``main`` function that performs the whole
# workflow, including writing the checksum file.
from code.data.fetch_nist_data import main as fetch_nist_main, OUTPUT_PATH

@pytest.mark.integration
def test_fetch_nist_data_produces_valid_output(tmp_path, monkeypatch):
    """
    Run the fetch script in a temporary directory to avoid polluting the
    repository. The test monkey‑patches the project root so that the script
    writes its output under ``tmp_path``.
    """
    # Redirect the output location to the temporary directory.
    temp_output = tmp_path / "nist_data.json"
    monkeypatch.setattr("code.data.fetch_nist_data.OUTPUT_PATH", temp_output)

    # Run the fetch workflow.
    fetch_nist_main()

    # 1. Output file exists.
    assert temp_output.is_file(), f"Expected output file {temp_output} not found."

    # 2. Record count >= 500.
    with temp_output.open("r", encoding="utf-8") as fp:
        records = [json.loads(line) for line in fp if line.strip()]
    assert len(records) >= 500, f"Only {len(records)} records were fetched; expected >= 500."

    # 3. Checksum verification.
    checksum_path = temp_output.with_suffix(".sha256")
    assert checksum_path.is_file(), "Checksum file missing."

    from utils.checksum import compute_sha256

    expected = checksum_path.read_text().strip()
    actual = compute_sha256(temp_output)
    assert expected == actual, "Checksum does not match the data file."