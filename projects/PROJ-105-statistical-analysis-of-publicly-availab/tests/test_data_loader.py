"""
Integration test for the data_loader module (Task T001).

The test verifies that:
1. ``download_bts_data`` successfully downloads the 2022 CSV from the verified mirror.
2. The expected ZIP archive ``On_Time_Reporting_CSV.zip`` exists in the correct location.
3. The ZIP archive contains the downloaded CSV file.
"""

import os
import zipfile
from pathlib import Path

import pytest

# Import the function under test
from data_loader import download_bts_data

@pytest.mark.parametrize("year", [2022])
def test_download_creates_zip(tmp_path: Path, year: int):
    """
    Download the 2022 dataset into a temporary directory and assert that the ZIP
    archive is created and contains the CSV file.
    """
    # Use a temporary subdirectory for the raw data
    output_dir = tmp_path / "raw" / str(year)

    # Perform the download
    csv_path = download_bts_data(year=year, output_dir=output_dir)

    # Verify the CSV was downloaded
    assert csv_path is not None
    assert csv_path.is_file()
    assert csv_path.name == f"bts_delays_{year}.csv"

    # Verify the ZIP archive exists
    zip_path = output_dir / "On_Time_Reporting_CSV.zip"
    assert zip_path.is_file(), f"Expected ZIP archive at {zip_path}"

    # Verify the ZIP contains the CSV file
    with zipfile.ZipFile(zip_path, "r") as zipf:
        zip_contents = zipf.namelist()
        assert csv_path.name in zip_contents, f"{csv_path.name} not found inside the ZIP archive"