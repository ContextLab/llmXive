import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv
import io

# Import the function to test
from code.data_loader import download_and_save_sample

class TestDataLoader:
    def test_download_and_save_sample_creates_file(self, tmp_path):
        """
        Test that download_and_save_sample creates the output file.
        We mock the load_dataset to avoid real network calls.
        """
        output_file = tmp_path / "test_sample.csv"
        
        mock_rows = [
            {"path": "file1.py", "content": "x = 1", "size": 100, "language": "python"},
            {"path": "file2.py", "content": "y = 2", "size": 100, "language": "python"},
        ]

        with patch("code.data_loader.load_dataset") as mock_load:
            # Create a mock iterator
            mock_iter = MagicMock()
            mock_iter.__iter__ = MagicMock(return_value=iter(mock_rows))
            mock_load.return_value = mock_iter

            result_path = download_and_save_sample(
                sample_size=2,
                path=output_file
            )

            assert result_path == output_file
            assert output_file.exists()
            
            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["path"] == "file1.py"
                assert rows[0]["content"] == "x = 1"

    def test_download_and_save_sample_fails_on_empty_dataset(self, tmp_path):
        """
        Test that the function raises RuntimeError if no rows are fetched.
        """
        output_file = tmp_path / "test_empty.csv"

        with patch("code.data_loader.load_dataset") as mock_load:
            # Create a mock iterator that yields nothing
            mock_iter = MagicMock()
            mock_iter.__iter__ = MagicMock(return_value=iter([]))
            mock_load.return_value = mock_iter

            with pytest.raises(RuntimeError, match="Failed to retrieve any rows"):
                download_and_save_sample(sample_size=1, path=output_file)

    def test_download_and_save_sample_invalid_size(self, tmp_path):
        """
        Test that ValueError is raised for non-positive sample_size.
        """
        with pytest.raises(ValueError, match="sample_size must be positive"):
            download_and_save_sample(sample_size=0)

        with pytest.raises(ValueError, match="sample_size must be positive"):
            download_and_save_sample(sample_size=-1)