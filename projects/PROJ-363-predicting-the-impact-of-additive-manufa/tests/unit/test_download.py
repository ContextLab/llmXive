import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from download_data import (
    fetch_record_metadata, 
    verify_material_type, 
    get_download_url,
    download_file,
    compute_file_hash
)

class TestDownloadData(unittest.TestCase):

    def test_verify_material_type_success(self):
        """Test that verification passes for 316L dataset."""
        metadata = {
            "metadata": {
                "title": "316L Stainless Steel LPBF Porosity Dataset",
                "description": "Experimental data for 316L stainless steel printed via LPBF.",
                "keywords": ["316L", "additive manufacturing", "porosity"]
            }
        }
        # Should not raise
        result = verify_material_type(metadata, "316L")
        self.assertTrue(result)

    def test_verify_material_type_failure(self):
        """Test that verification fails for non-316L dataset."""
        metadata = {
            "metadata": {
                "title": "Permafrost Toxic Elements",
                "description": "Study on mobilization of toxic elements from permafrost.",
                "keywords": ["environment", "permafrost"]
            }
        }
        with self.assertRaises(ValueError) as context:
            verify_material_type(metadata, "316L")
        self.assertIn("Material mismatch", str(context.exception))

    @patch('urllib.request.urlopen')
    def test_download_file_network_failure(self, mock_urlopen):
        """Test that download_file raises RuntimeError on network failure and produces NO file."""
        # Simulate a network error (e.g., timeout, connection refused)
        mock_urlopen.side_effect = Exception("Network error: Connection timed out")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "should_not_exist.csv")
            
            # Verify file does not exist before call
            self.assertFalse(os.path.exists(output_path))
            
            # Expect RuntimeError
            with self.assertRaises(RuntimeError) as context:
                download_file("http://fake-url.com/file.csv", output_path)
            
            # Verify error message indicates failure
            self.assertIn("Download failed", str(context.exception))
            
            # CRITICAL: Verify NO file was created (no synthetic fallback)
            self.assertFalse(os.path.exists(output_path), 
                             "download_file must NOT produce a synthetic file on failure")

    @patch('urllib.request.urlopen')
    def test_download_file_http_error(self, mock_urlopen):
        """Test that download_file raises RuntimeError on HTTP 404."""
        from urllib.error import HTTPError
        
        # Simulate HTTP 404
        mock_urlopen.side_effect = HTTPError("http://fake-url.com/file.csv", 404, "Not Found", {}, None)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "should_not_exist.csv")
            
            with self.assertRaises(RuntimeError) as context:
                download_file("http://fake-url.com/file.csv", output_path)
            
            self.assertIn("Download failed", str(context.exception))
            self.assertFalse(os.path.exists(output_path))

    def test_compute_file_hash(self):
        """Test that checksum is computed correctly."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        try:
            hash_val = compute_file_hash(tmp_path)
            self.assertEqual(len(hash_val), 64) # SHA-256 hex length
            self.assertIsInstance(hash_val, str)
        finally:
            os.unlink(tmp_path)

    def test_download_file_success_creates_file(self):
        """Test that download_file creates the file on success."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            # Mock a successful response
            mock_response = MagicMock()
            mock_response.read.return_value = b"csv,data\n1,2"
            mock_response.__enter__ = lambda s: s
            mock_response.__exit__ = lambda s, *args: None
            mock_urlopen.return_value = mock_response
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test.csv")
                
                # This should succeed
                download_file("http://fake-url.com/file.csv", output_path)
                
                # Verify file exists and has content
                self.assertTrue(os.path.exists(output_path))
                with open(output_path, 'rb') as f:
                    content = f.read()
                self.assertEqual(content, b"csv,data\n1,2")

    if __name__ == '__main__':
        unittest.main()