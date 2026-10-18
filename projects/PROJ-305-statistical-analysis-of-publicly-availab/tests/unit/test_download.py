import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the repository's code directory to sys.path so we can import src.data.download
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from src.data.download import (
    BASE_URL,
    FILE_TYPES,
    YEARS,
    download_year,
    sha256_checksum,
)

@pytest.fixture
def fake_zip(tmp_path):
    """Create a minimal zip containing a single CSV file."""
    import zipfile
    csv_content = b"id,value\n1,foo\n2,bar\n"
    zip_path = tmp_path / "2020VAERSDATA.csv.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("2020VAERSDATA.csv", csv_content)
    return zip_path

def test_sha256_checksum(tmp_path):
    # Write a known file
    file_path = tmp_path / "test.txt"
    file_path.write_bytes(b"abc")
    expected = hashlib.sha256(b"abc").hexdigest()
    assert sha256_checksum(file_path) == expected

@patch("src.data.download.download_zip")
@patch("src.data.download.extract_zip")
def test_download_year_success(mock_extract, mock_download, tmp_path):
    """
    Verify that ``download_year`` calls the expected helpers and records
    checksums without raising.
    """
    # Mock the zip download – we don't hit the network
    mock_download.return_value = None

    # Mock extraction – return a list with a single dummy CSV Path
    dummy_csv = tmp_path / "2020VAERSDATA.csv"
    dummy_csv.write_text("id,value\n1,foo")
    mock_extract.return_value = [dummy_csv]

    # Run the function; it should complete without exception
    result = download_year(2020)

    # Ensure each FILE_TYPE key is present and maps to the dummy CSV list
    for ft in FILE_TYPES:
        assert ft in result
        assert dummy_csv in result[ft]

    # Verify that checksum file was written
    checksums_path = Path("data/checksums.txt")
    assert checksums_path.exists()
    lines = checksums_path.read_text().splitlines()
    # At least one line should contain the dummy CSV name and OK flag
    assert any("OK" in line for line in lines)

@patch("src.data.download.download_zip", side_effect=Exception("404"))
def test_download_year_failure(mock_download):
    """If the zip cannot be retrieved the function must raise."""
    with pytest.raises(SystemExit):
        download_year(2020)