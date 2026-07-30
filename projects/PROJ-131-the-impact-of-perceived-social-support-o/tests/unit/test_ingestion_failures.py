import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the function to test
from code.data.ingestion import download_dataset, load_cyber_data, main

class TestIngestionFailures:
    """
    Tests to verify that the ingestion pipeline fails loudly when real data fetch fails,
    and does not fall back to synthetic data.
    """

    def test_download_dataset_raises_on_failure(self):
        """
        Test that download_dataset raises RuntimeError if the URL is invalid or network fails.
        It must NOT return a mock dataframe or synthetic data.
        """
        invalid_url = "https://invalid-url-that-does-not-exist-12345.com/data.zip"
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "data.zip"
            
            with pytest.raises(RuntimeError) as exc_info:
                download_dataset(invalid_url, dest_path)
            
            assert "Real data fetch failed" in str(exc_info.value)
            assert "Aborting to prevent synthetic data fabrication" in str(exc_info.value)
            assert not dest_path.exists()

    @patch('code.data.ingestion.urllib.request.urlopen')
    def test_download_dataset_raises_on_http_error(self, mock_urlopen):
        """
        Test that download_dataset raises RuntimeError on HTTP errors (e.g., 404, 500).
        """
        mock_urlopen.side_effect = Exception("HTTP 404 Not Found")
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_path = Path(tmp_dir) / "data.zip"
            
            with pytest.raises(RuntimeError) as exc_info:
                download_dataset("http://example.com/data.zip", dest_path)
            
            assert "Real data fetch failed" in str(exc_info.value)

    def test_load_cyber_data_raises_on_missing_file(self):
        """
        Test that load_cyber_data raises FileNotFoundError if the file does not exist.
        """
        non_existent_path = Path("/tmp/does_not_exist_12345.csv")
        with pytest.raises(FileNotFoundError):
            load_cyber_data(non_existent_path)

    def test_no_synthetic_fallback_in_main(self):
        """
        Integration test: Verify that main() raises an error if download fails,
        rather than proceeding with synthetic data.
        """
        # Mock download_dataset to raise an error
        with patch('code.data.ingestion.download_dataset') as mock_download:
            mock_download.side_effect = RuntimeError("Real data fetch failed. Aborting to prevent synthetic data fabrication.")
            
            # Ensure directories exist for the test
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Patch the global paths to use temp dir
                import code.data.ingestion as ingestion_module
                original_raw_dir = ingestion_module.RAW_DATA_DIR
                original_processed_dir = ingestion_module.PROCESSED_DATA_DIR
                
                ingestion_module.RAW_DATA_DIR = Path(tmp_dir)
                ingestion_module.PROCESSED_DATA_DIR = Path(tmp_dir) / "processed"
                
                try:
                    with pytest.raises(RuntimeError) as exc_info:
                        # We need to mock the existence check too so it tries to download
                        with patch.object(ingestion_module.Path, 'exists', return_value=False):
                            ingestion_module.main()
                    
                    assert "Real data fetch failed" in str(exc_info.value)
                finally:
                    # Restore original paths
                    ingestion_module.RAW_DATA_DIR = original_raw_dir
                    ingestion_module.PROCESSED_DATA_DIR = original_processed_dir