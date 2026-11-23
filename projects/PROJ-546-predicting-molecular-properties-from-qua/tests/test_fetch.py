"""
Contract tests for code/fetch_data.py.

These tests verify the core functionality of the data fetching pipeline
without necessarily downloading the full dataset every time (using mocks
for network calls where appropriate, but verifying the logic).
"""
import os
import tempfile
import hashlib
import io
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open
import tarfile
import csv
import sys

# Import the module under test
# We need to adjust the import path if necessary, but assuming standard structure
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetch_data import compute_sha256, download_file, extract_tarball, convert_to_csv, main


class TestChecksum:
    def test_compute_sha256_known_value(self):
        """Test SHA256 computation with a known string."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # "test content" SHA256 is known
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            actual = compute_sha256(Path(temp_path))
            assert actual == expected
        finally:
            os.unlink(temp_path)


class TestConversion:
    def test_convert_to_csv_from_tsv(self):
        """Test conversion from TSV to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "data.tsv"
            output = tmpdir / "output.csv"

            # Create a mock TSV file
            with open(source, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['molecule_id', 'smiles', 'experimental_barrier'])
                writer.writerow(['mol1', 'CCO', '45.2'])
                writer.writerow(['mol2', 'CC', '30.1'])

            convert_to_csv(tmpdir, output)

            assert output.exists()
            with open(output, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['smiles'] == 'CCO'
                assert rows[1]['experimental_barrier'] == '30.1'

class TestMainIntegration:
    @patch('fetch_data.requests.get')
    @patch('fetch_data.logger')
    def test_main_with_mocked_download(self, mock_logger, mock_get):
        """Test the main flow with mocked network calls and file operations."""
        # Setup mock for metadata response
        mock_meta_response = MagicMock()
        mock_meta_response.json.return_value = {
            'files': [
                {
                    'key': 'data.tar.gz',
                    'links': {'self': 'http://example.com/file'}
                }
            ]
        }

        # Setup mock for file download response
        mock_file_response = MagicMock()
        mock_file_response.iter_content.return_value = [b"fake tarball content"]
        mock_get.side_effect = [mock_meta_response, mock_file_response]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Patch the global constants to use temp directories
            import fetch_data
            original_output_dir = fetch_data.OUTPUT_DIR
            original_output_csv = fetch_data.OUTPUT_CSV
            fetch_data.OUTPUT_DIR = tmpdir
            fetch_data.OUTPUT_CSV = tmpdir / "test.csv"

            # We also need to patch the checksum to avoid failure
            # Since we are using fake content, the checksum won't match the real one.
            # We will patch the EXPECTED_CHECKSUM to match the fake content hash.
            fake_content = b"fake tarball content"
            fake_checksum = hashlib.sha256(fake_content).hexdigest()
            fetch_data.EXPECTED_CHECKSUM = fake_checksum

            try:
                # Mock the tar extraction to do nothing (or create a fake file)
                with patch('tarfile.open') as mock_tar_open:
                    mock_tar = MagicMock()
                    mock_tar.__enter__ = MagicMock(return_value=mock_tar)
                    mock_tar.__exit__ = MagicMock(return_value=False)
                    mock_tar.extractall = MagicMock()
                    mock_tar_open.return_value = mock_tar

                    # Mock convert_to_csv to just create an empty file
                    with patch('fetch_data.convert_to_csv') as mock_convert:
                        mock_convert.side_effect = lambda src, dst: Path(dst).touch()

                        try:
                            main()
                            assert fetch_data.OUTPUT_CSV.exists()
                        except ValueError as e:
                            if "Checksum verification failed" in str(e):
                                pytest.fail("Checksum verification failed with mocked content")
                            raise
            finally:
                fetch_data.OUTPUT_DIR = original_output_dir
                fetch_data.OUTPUT_CSV = original_output_csv

if __name__ == "__main__":
    pytest.main([__file__, "-v"])