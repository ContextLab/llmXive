"""
Unit tests for fetch_mp_perovskites.py (T012b)
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from fetch_mp_perovskites import fetch_mp_material_data, fetch_experimental_tga_data, validate_data_checksum

class TestFetchMpPerovskites(unittest.TestCase):

    @patch('fetch_mp_perovskites.fetch_with_retry')
    def test_fetch_mp_material_data_success(self, mock_fetch):
        """Test successful fetch of material data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'material_id': 'mp-12345'}}
        mock_fetch.return_value = mock_response

        result = fetch_mp_material_data("CsPbI3", "fake_api_key")
        self.assertIsNotNone(result)
        self.assertEqual(result['material_id'], 'mp-12345')
        mock_fetch.assert_called_once()

    @patch('fetch_mp_perovskites.fetch_with_retry')
    def test_fetch_mp_material_data_failure(self, mock_fetch):
        """Test failed fetch of material data."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_fetch.return_value = mock_response

        result = fetch_mp_material_data("CsPbI3", "fake_api_key")
        self.assertIsNone(result)

    @patch('fetch_mp_perovskites.fetch_with_retry')
    def test_fetch_experimental_tga_data_success(self, mock_fetch):
        """Test successful fetch of experimental TGA data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'experiment_type': 'TGA', 'onset_temp': 300}]}
        mock_fetch.return_value = mock_response

        result = fetch_experimental_tga_data("mp-12345", "fake_api_key")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['experiment_type'], 'TGA')
        self.assertEqual(result[0]['onset_temp'], 300)

    @patch('fetch_mp_perovskites.fetch_with_retry')
    def test_fetch_experimental_tga_data_failure(self, mock_fetch):
        """Test failed fetch of experimental TGA data."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_fetch.return_value = mock_response

        result = fetch_experimental_tga_data("mp-12345", "fake_api_key")
        self.assertEqual(result, [])

    def test_validate_data_checksum(self):
        """Test data checksum validation."""
        data = {'key': 'value'}
        import hashlib
        import json
        expected_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()
        
        self.assertTrue(validate_data_checksum(data, expected_hash))
        self.assertFalse(validate_data_checksum(data, "wrong_hash"))

if __name__ == '__main__':
    unittest.main()