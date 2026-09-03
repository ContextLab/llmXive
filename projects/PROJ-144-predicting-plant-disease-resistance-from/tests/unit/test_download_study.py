import os
import json
import tempfile
import zipfile
import io
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: Assuming the test runs from the project root or code directory is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.download_study import download_study_data, compute_checksums, download_study

def test_download_study_data_extraction():
    """
    Test that download_study_data correctly extracts CSVs from a mock zip.
    """
    # Create a mock zip in memory
    mock_zip_buffer = io.BytesIO()
    with zipfile.ZipFile(mock_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as mock_zip:
        # Create mock CSV content
        intensity_data = "metabolite_1,metabolite_2\n10.5,20.3\n11.2,21.0"
        phenotype_data = "sample_id,resistance\nS1,Resistant\nS2,Susceptible"
        
        mock_zip.writestr("study_123_intensity.csv", intensity_data)
        mock_zip.writestr("study_123_phenotype.csv", phenotype_data)

    mock_zip_buffer.seek(0)

    with patch('data.download_study.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.content = mock_zip_buffer.getvalue()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            result = download_study_data("https://mock.url", output_dir)

            assert "intensity" in result
            assert "phenotype" in result
            assert os.path.exists(result["intensity"])
            assert os.path.exists(result["phenotype"])

            # Verify content
            with open(result["intensity"], 'r') as f:
                assert "metabolite_1" in f.read()
            with open(result["phenotype"], 'r') as f:
                assert "resistance" in f.read()

def test_compute_checksums():
    """
    Test SHA256 checksum computation.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test.txt"
        test_file.write_text("Hello, World!")

        checksums = compute_checksums([str(test_file)])
        
        assert str(test_file) in checksums
        assert checksums[str(test_file)] == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

def test_download_study_failure():
    """
    Test that download_study handles network errors gracefully.
    """
    with patch('data.download_study.requests.get') as mock_get:
        mock_get.side_effect = Exception("Network Error")

        result = download_study("ST000001", "https://bad.url", Path("data/raw"))
        
        assert result["status"] == "failed"
        assert "Network Error" in result["error"]

def test_download_study_empty_zip():
    """
    Test that download_study_data raises error on empty/invalid zip.
    """
    mock_zip_buffer = io.BytesIO()
    with zipfile.ZipFile(mock_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as mock_zip:
        # Write nothing or non-CSV
        mock_zip.writestr("readme.txt", "No data here")

    mock_zip_buffer.seek(0)

    with patch('data.download_study.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.content = mock_zip_buffer.getvalue()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            with pytest.raises(ValueError, match="No CSV files found"):
                download_study_data("https://mock.url", output_dir)
