"""
Unit tests for dataset ingestion validator (code/ingestion/validate_source.py).

These tests verify the logic of the validator without requiring network access
for every assertion, though they mock the network behavior to ensure the
abort-on-mismatch logic works correctly.
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Add code directory to path for imports
sys.path.insert(0, 'code')

from ingestion.validate_source import (
    check_dataset_availability,
    verify_dataset_structure,
    validate_source,
    EXPECTED_DATASET_ID,
    OPENNEURO_API_BASE
)

class TestCheckDatasetAvailability(unittest.TestCase):
    """Tests for the check_dataset_availability function."""

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_dataset_available(self, mock_urlopen):
        """Test that available dataset returns True."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = check_dataset_availability("ds001734")
        self.assertTrue(result)

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_dataset_not_found(self, mock_urlopen):
        """Test that 404 returns False."""
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(url="", code=404, msg="", hdrs=None, fp=None)

        result = check_dataset_availability("ds000000")
        self.assertFalse(result)

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_server_error_returns_false(self, mock_urlopen):
        """Test that 500 error returns False (treated as failure for validation)."""
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(url="", code=500, msg="", hdrs=None, fp=None)

        result = check_dataset_availability("ds001734")
        self.assertFalse(result)

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_timeout_returns_false(self, mock_urlopen):
        """Test that timeout returns False."""
        mock_urlopen.side_effect = Exception("Timeout")

        result = check_dataset_availability("ds001734")
        self.assertFalse(result)

class TestVerifyDatasetStructure(unittest.TestCase):
    """Tests for the verify_dataset_structure function."""

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_valid_structure_with_func(self, mock_urlopen):
        """Test that structure with sub- and func directories returns True."""
        # Mock the root tree response
        mock_root_response = MagicMock()
        mock_root_response.status = 200
        root_data = {
            "nodes": [
                {"name": "sub-01"},
                {"name": "sub-02"},
                {"name": "dataset_description.json"}
            ]
        }
        mock_root_response.read.return_value = json.dumps(root_data).encode('utf-8')

        # Mock the subject tree response (first sub-01)
        mock_sub_response = MagicMock()
        mock_sub_response.status = 200
        sub_data = {
            "nodes": [
                {"name": "func"},
                {"name": "anat"}
            ]
        }
        mock_sub_response.read.return_value = json.dumps(sub_data).encode('utf-8')

        # Configure side_effect to return root first, then sub response
        mock_urlopen.side_effect = [mock_root_response, mock_sub_response]

        result = verify_dataset_structure("ds001734")
        self.assertTrue(result)

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_invalid_structure_no_sub_dirs(self, mock_urlopen):
        """Test that structure without sub- directories returns False."""
        mock_root_response = MagicMock()
        mock_root_response.status = 200
        root_data = {
            "nodes": [
                {"name": "dataset_description.json"}
            ]
        }
        mock_root_response.read.return_value = json.dumps(root_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_root_response

        result = verify_dataset_structure("ds001734")
        self.assertFalse(result)

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_invalid_structure_no_func_dirs(self, mock_urlopen):
        """Test that structure with sub- but no func returns False."""
        # Mock root
        mock_root_response = MagicMock()
        mock_root_response.status = 200
        root_data = {"nodes": [{"name": "sub-01"}]}
        mock_root_response.read.return_value = json.dumps(root_data).encode('utf-8')

        # Mock sub (no func)
        mock_sub_response = MagicMock()
        mock_sub_response.status = 200
        sub_data = {"nodes": [{"name": "anat"}]}
        mock_sub_response.read.return_value = json.dumps(sub_data).encode('utf-8')

        mock_urlopen.side_effect = [mock_root_response, mock_sub_response]

        result = verify_dataset_structure("ds001734")
        self.assertFalse(result)

    @patch('ingestion.validate_source.urllib.request.urlopen')
    def test_api_error_returns_false(self, mock_urlopen):
        """Test that API error returns False."""
        mock_urlopen.side_effect = Exception("API Error")
        result = verify_dataset_structure("ds001734")
        self.assertFalse(result)

class TestValidateSource(unittest.TestCase):
    """Tests for the main validate_source function."""

    def test_dataset_id_mismatch(self):
        """Test that wrong dataset ID returns False."""
        result = validate_source("ds000224")
        self.assertFalse(result)

    def test_correct_id_with_failures(self):
        """Test that correct ID but failed availability returns False."""
        with patch('ingestion.validate_source.check_dataset_availability', return_value=False):
            result = validate_source(EXPECTED_DATASET_ID)
            self.assertFalse(result)

    def test_correct_id_with_structure_failures(self):
        """Test that correct ID, available, but bad structure returns False."""
        with patch('ingestion.validate_source.check_dataset_availability', return_value=True):
            with patch('ingestion.validate_source.verify_dataset_structure', return_value=False):
                result = validate_source(EXPECTED_DATASET_ID)
                self.assertFalse(result)

    def test_full_success(self):
        """Test that correct ID, available, and good structure returns True."""
        with patch('ingestion.validate_source.check_dataset_availability', return_value=True):
            with patch('ingestion.validate_source.verify_dataset_structure', return_value=True):
                result = validate_source(EXPECTED_DATASET_ID)
                self.assertTrue(result)

class TestMain(unittest.TestCase):
    """Tests for the main entry point logic."""

    @patch('sys.exit')
    @patch('ingestion.validate_source.validate_source')
    def test_main_success_exits_0(self, mock_validate, mock_exit):
        """Test that main exits with 0 on success."""
        mock_validate.return_value = True
        
        from ingestion.validate_source import main
        main()
        
        mock_exit.assert_called_once_with(0)

    @patch('sys.exit')
    @patch('ingestion.validate_source.validate_source')
    def test_main_failure_exits_1(self, mock_validate, mock_exit):
        """Test that main exits with 1 on failure."""
        mock_validate.return_value = False
        
        from ingestion.validate_source import main
        main()
        
        mock_exit.assert_called_once_with(1)

    @patch('sys.argv', ['validate_source.py', 'ds000000'])
    @patch('sys.exit')
    @patch('ingestion.validate_source.validate_source')
    def test_main_with_arg(self, mock_validate, mock_exit):
        """Test that main passes command line argument to validate_source."""
        mock_validate.return_value = False
        
        from ingestion.validate_source import main
        main()
        
        mock_validate.assert_called_once_with('ds000000')

if __name__ == '__main__':
    unittest.main()