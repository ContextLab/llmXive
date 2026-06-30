"""Integration test for the data loader.

The test ensures that ``download_and_save_sample`` creates the expected CSV
file and that the file contains at least one data row.  It is deliberately
lightweight to keep CI runtimes short.
"""

import csv
from pathlib import Path

import pytest

from code.data_loader import download_and_save_sample

@pytest.mark.integration
def test_download_and_save_sample_creates_csv(tmp_path: Path) -> None:
    # Use a temporary directory to avoid polluting the repository data folder.
    csv_path = tmp_path / "sample.csv"
    result_path = download_and_save_sample(raw_csv_path=csv_path, num_examples=10)

    # The function should return the absolute path to the file we asked for.
    assert result_path == csv_path.resolve()
    assert csv_path.is_file()

    # Verify that the CSV has a header and at least one data row.
    with csv_path.open(newline="") as f:
        rows = list(csv.reader(f))
    assert rows, "CSV should not be empty"
    assert rows[0] == ["repo_name", "content"], "Header row mismatch"
    assert len(rows) > 1, "CSV should contain at least one data row"