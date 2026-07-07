"""
Unit tests for manifest validation logic.

Tests the data validation logic found in code/00_verify_manifest.py
and the verification logic used by code/01_download_data.sh.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

# Import the real functions from the existing API surface
from verify_manifest import check_ncbi_accession, verify_manifest

class TestManifestValidation(unittest.TestCase):

    def test_check_ncbi_accession_valid(self):
        """Test that a known valid accession returns True."""
        # Mock the network response to simulate a valid accession
        with patch('verify_manifest.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            # Simulate NCBI EInfo or similar JSON response indicating existence
            mock_response.read.return_value = b'{"result": {"12345": {"status": "live"}}}'
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            result = check_ncbi_accession("12345")
            self.assertTrue(result)

    def test_check_ncbi_accession_invalid(self):
        """Test that an invalid accession returns False."""
        with patch('verify_manifest.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            # Simulate empty result or error
            mock_response.read.return_value = b'{"result": {}}'
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            result = check_ncbi_accession("INVALID_ID")
            self.assertFalse(result)

    def test_check_ncbi_accession_network_error(self):
        """Test that network errors are handled gracefully."""
        with patch('verify_manifest.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network Error")
            
            result = check_ncbi_accession("12345")
            self.assertFalse(result)

    def test_verify_manifest_missing_file(self):
        """Test that verify_manifest returns False if file is missing."""
        # We test the logic by mocking os.path.exists to return False
        with patch('verify_manifest.os.path.exists', return_value=False):
            result = verify_manifest()
            self.assertFalse(result)

    def test_verify_manifest_invalid_yaml(self):
        """Test that verify_manifest returns False for invalid YAML."""
        invalid_yaml_content = "invalid: yaml: content: ["
        
        with patch('verify_manifest.open', mock_open(read_data=invalid_yaml_content)):
            with patch('verify_manifest.os.path.exists', return_value=True):
                # Mock yaml.safe_load to raise an error
                with patch('verify_manifest.yaml.safe_load', side_effect=Exception("YAML Error")):
                    result = verify_manifest()
                    self.assertFalse(result)

    def test_verify_manifest_missing_data_sources(self):
        """Test that verify_manifest returns False if 'data_sources' key is missing."""
        valid_yaml_missing_key = "version: 1.0\nother_key: value"
        
        with patch('verify_manifest.open', mock_open(read_data=valid_yaml_missing_key)):
            with patch('verify_manifest.os.path.exists', return_value=True):
                result = verify_manifest()
                self.assertFalse(result)

    def test_verify_manifest_valid_structure(self):
        """Test that verify_manifest returns True for valid structure."""
        valid_yaml = """
        version: 1.0
        data_sources:
          chipseq:
            - accession: GSE12345
              type: ChIP-seq
          eqtl:
            - accession: GSE54321
              type: eQTL
        """
        
        with patch('verify_manifest.open', mock_open(read_data=valid_yaml)):
            with patch('verify_manifest.os.path.exists', return_value=True):
                # Ensure yaml.safe_load returns the parsed dict
                parsed_data = {
                    "version": "1.0",
                    "data_sources": {
                        "chipseq": [{"accession": "GSE12345", "type": "ChIP-seq"}],
                        "eqtl": [{"accession": "GSE54321", "type": "eQTL"}]
                    }
                }
                with patch('verify_manifest.yaml.safe_load', return_value=parsed_data):
                    result = verify_manifest()
                    self.assertTrue(result)

    def test_verify_manifest_empty_data_sources(self):
        """Test that verify_manifest returns False if data_sources is empty."""
        valid_yaml_empty = """
        version: 1.0
        data_sources: {}
        """
        
        with patch('verify_manifest.open', mock_open(read_data=valid_yaml_empty)):
            with patch('verify_manifest.os.path.exists', return_value=True):
                parsed_data = {"version": "1.0", "data_sources": {}}
                with patch('verify_manifest.yaml.safe_load', return_value=parsed_data):
                    result = verify_manifest()
                    self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()