"""
Unit tests for the MEG data download module.
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Import the function to test
from src.data.download_meg import download_meg_streamed

def test_download_meg_streamed_creates_file():
    """
    Test that the download function creates the expected parquet file
    and the file contains more than 1000 rows.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "meg_streamed.parquet"
        
        # Mock the load_dataset to return a known structure that yields enough rows
        mock_data = [
            {"meg": list(range(10)), "subject": "01", "row_id": i}
            for i in range(1500)
        ]
        
        with patch("src.data.download_meg.load_dataset") as mock_load:
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = lambda self: iter(mock_data)
            mock_load.return_value = mock_dataset
            
            # Call the function
            result_path = download_meg_streamed(tmp_dir)
            
            # Assertions
            assert os.path.exists(result_path)
            df = pd.read_parquet(result_path)
            assert len(df) > 1000
            assert "row_id" in df.columns

def test_download_meg_streamed_empty_dataset():
    """
    Test that the function raises an error if the dataset yields no data.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("src.data.download_meg.load_dataset") as mock_load:
            mock_dataset = MagicMock()
            mock_dataset.__iter__ = lambda self: iter([])
            mock_load.return_value = mock_dataset
            
            with pytest.raises(ValueError, match="No data rows extracted"):
                download_meg_streamed(tmp_dir)