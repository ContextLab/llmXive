"""
Integration test for the Materials Project data fetcher (T005a).

The test runs the fetcher script and verifies that:
  1. The expected output file exists.
  2. The file contains at least `MIN_ROWS` records.
  3. The accompanying SHA‑256 checksum file matches the content.

This test is deliberately lightweight: it relies on the real fallback
dataset (matbench) if no valid Materials Project API key is available.
"""

import json
from pathlib import Path

import pytest

from data.fetch_materials import main as fetch_main
from utils.checksum import compute_sha256

# The fetcher guarantees a minimum of 5 000 rows; we expose the constant
# via the module for the test.
from data.fetch_materials import MIN_ROWS


@pytest.mark.integration
def test_fetch_materials_produces_valid_output(tmp_path, monkeypatch):
    """
    Run the fetcher and validate the produced JSON and checksum.
    """
    # Redirect the output location to a temporary directory to avoid polluting
    # the repository state.
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "pathlib.Path.cwd",
        lambda: tmp_path,
    )
    # Ensure the script writes to the temporary location.
    monkeypatch.setattr(
        "code.data.fetch_materials.Path",
        lambda *args, **kwargs: Path(tmp_path, *args),
    )

    # Execute the fetcher.
    fetch_main()

    output_path = tmp_path / "data" / "raw" / "materials_project_data.json"
    checksum_path = output_path.with_suffix(".sha256")

    # 1. Output file must exist.
    assert output_path.is_file(), f"{output_path} was not created."

    # 2. Load JSON and check row count.
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "Fetched data should be a list of records."
    assert (
        len(data) >= MIN_ROWS
    ), f"Expected at least {MIN_ROWS} rows, got {len(data)}."

    # 3. Verify checksum matches.
    expected_checksum = compute_sha256(output_path)
    actual_checksum = checksum_path.read_text(encoding="utf-8").strip()
    assert (
        expected_checksum == actual_checksum
    ), "Checksum mismatch for fetched materials data."