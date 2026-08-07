import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import yaml
from pathlib import Path

# Import the module to test
from download import (
    fetch_with_retry_rate_limit,
    fetch_materials_with_thermal_conductivity,
    fetch_cif_content,
    compute_sha256,
    update_metadata_snapshot,
    download_cif_files
)

class TestDownload(unittest.TestCase):
    
    @patch('download.requests.get')
    def test_fetch_with_retry_rate_limit_success(self, mock_get):
        """Test successful fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"material_id": "MP-123"}]}
        mock_get.return_value = mock_response
        
        result = fetch_with_retry_rate_limit("http://test.com", {})
        self.assertIsNotNone(result)
        self.assertEqual(result["data"][0]["material_id"], "MP-123")

    @patch('download.requests.get')
    def test_fetch_with_retry_rate_limit_rate_limit(self, mock_get):
        """Test fetch with rate limiting."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": [{"material_id": "MP-123"}]}
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        result = fetch_with_retry_rate_limit("http://test.com", {})
        self.assertIsNotNone(result)
        self.assertEqual(len(mock_get.call_args_list), 2)

    def test_compute_sha256(self):
        """Test SHA256 checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_sha256(temp_path)
            self.assertEqual(len(checksum), 64) # SHA256 hex is 64 chars
        finally:
            os.unlink(temp_path)

    @patch('download.fetch_with_retry_rate_limit')
    def test_fetch_materials_with_thermal_conductivity(self, mock_fetch):
        """Test fetching materials with thermal conductivity."""
        mock_fetch.return_value = {
            "data": [
                {"material_id": "MP-123", "thermal_conductivity": {"k_xx": 10.0}}
            ]
        }
        
        result = fetch_materials_with_thermal_conductivity("fake_key", limit=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["material_id"], "MP-123")

    def test_update_metadata_snapshot(self):
        """Test updating metadata snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = os.path.join(tmpdir, "metadata.yaml")
            
            update_metadata_snapshot(metadata_path, "MP-123", "data/raw/cif/MP-123.cif", "checksum123")
            
            self.assertTrue(os.path.exists(metadata_path))
            
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
            
            self.assertEqual(len(metadata["materials"]), 1)
            self.assertEqual(metadata["materials"][0]["material_id"], "MP-123")
            self.assertEqual(metadata["materials"][0]["cif_checksum"], "checksum123")

    @patch('download.fetch_materials_with_thermal_conductivity')
    @patch('download.fetch_cif_content')
    @patch('download.compute_sha256')
    @patch('download.update_metadata_snapshot')
    def test_download_cif_files(self, mock_update, mock_sha, mock_fetch_cif, mock_fetch_materials):
        """Test downloading CIF files."""
        mock_fetch_materials.return_value = [{"material_id": "MP-123"}]
        mock_fetch_cif.return_value = "cif_content"
        mock_sha.return_value = "checksum123"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            count = download_cif_files(tmpdir, limit=1, metadata_path=os.path.join(tmpdir, "meta.yaml"))
            
            self.assertEqual(count, 1)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "MP-123.cif")))

if __name__ == "__main__":
    unittest.main()
