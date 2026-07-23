"""
Unit tests for data retrieval logic in code/data/retrieval.py.

These tests verify the core functionality of the Caco-2 data retrieval process,
including API response parsing, record extraction, and data validation.
"""
import unittest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import csv
import io

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.retrieval import fetch_assay_page, extract_records, write_raw_data


class TestFetchAssayPage(unittest.TestCase):
    """Tests for the fetch_assay_page function."""

    @patch('data.retrieval.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful API fetch with valid JSON response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "assay_chemblId": "CHEMBL123",
            "assay_type": "Caco-2",
            "results": [{"standard_value": "1.5", "standard_units": "cm/s"}]
        }
        mock_get.return_value = mock_response

        # Call function
        result = fetch_assay_page(1)

        # Verify request was made
        mock_get.assert_called_once()
        self.assertEqual(result, mock_response.json.return_value)

    @patch('data.retrieval.requests.get')
    def test_rate_limit_handling(self, mock_get):
        """Test that rate limiting (429) is handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            fetch_assay_page(1)

    @patch('data.retrieval.requests.get')
    def test_invalid_json(self, mock_get):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            fetch_assay_page(1)


class TestExtractRecords(unittest.TestCase):
    """Tests for the extract_records function."""

    def test_extract_valid_records(self):
        """Test extraction of valid records from assay data."""
        assay_data = {
            "assay_chemblId": "CHEMBL123",
            "assay_type": "Caco-2",
            "assay_organism": "Homo sapiens",
            "results": [
                {
                    "molecule_chemblId": "CHEMBL456",
                    "standard_type": "MEASUREMENT",
                    "standard_value": "1.5",
                    "standard_units": "cm/s",
                    "structure_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
                },
                {
                    "molecule_chemblId": "CHEMBL789",
                    "standard_type": "MEASUREMENT",
                    "standard_value": "2.0",
                    "standard_units": "cm/s",
                    "structure_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
                }
            ]
        }

        records = extract_records(assay_data)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["assay_id"], "CHEMBL123")
        self.assertEqual(records[0]["molecule_id"], "CHEMBL456")
        self.assertEqual(records[0]["logPapp"], "1.5")
        self.assertEqual(records[0]["SMILES"], "CC(=O)OC1=CC=CC=C1C(=O)O")

    def test_extract_missing_fields(self):
        """Test extraction when some fields are missing."""
        assay_data = {
            "assay_chemblId": "CHEMBL123",
            "assay_type": "Caco-2",
            "results": [
                {
                    "molecule_chemblId": "CHEMBL456",
                    "standard_type": "MEASUREMENT",
                    "standard_value": "1.5",
                    "standard_units": "cm/s"
                    # Missing structure_smiles
                }
            ]
        }

        records = extract_records(assay_data)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["SMILES"], "")  # Should be empty string

    def test_extract_non_measurement_records(self):
        """Test that non-MEASUREMENT records are excluded."""
        assay_data = {
            "assay_chemblId": "CHEMBL123",
            "assay_type": "Caco-2",
            "results": [
                {
                    "molecule_chemblId": "CHEMBL456",
                    "standard_type": "CALCULATED",
                    "standard_value": "1.5",
                    "standard_units": "cm/s",
                    "structure_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
                },
                {
                    "molecule_chemblId": "CHEMBL789",
                    "standard_type": "MEASUREMENT",
                    "standard_value": "2.0",
                    "standard_units": "cm/s",
                    "structure_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"
                }
            ]
        }

        records = extract_records(assay_data)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["molecule_id"], "CHEMBL789")


class TestWriteRawData(unittest.TestCase):
    """Tests for the write_raw_data function."""

    def test_write_valid_data(self):
        """Test writing valid data to CSV file."""
        records = [
            {"assay_id": "CHEMBL123", "molecule_id": "CHEMBL456", "logPapp": "1.5", "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O"},
            {"assay_id": "CHEMBL123", "molecule_id": "CHEMBL789", "logPapp": "2.0", "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O"}
        ]
        
        output_path = Path("/tmp/test_retrieval_output.csv")
        
        # Write data
        write_raw_data(records, str(output_path))
        
        # Verify file was created
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["SMILES"], "CC(=O)OC1=CC=CC=C1C(=O)O")
            
        # Cleanup
        output_path.unlink()

    def test_write_empty_data(self):
        """Test writing empty data list."""
        records = []
        output_path = Path("/tmp/test_retrieval_empty.csv")
        
        # Write data
        write_raw_data(records, str(output_path))
        
        # Verify file was created
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 0)
            
        # Cleanup
        output_path.unlink()


if __name__ == "__main__":
    unittest.main()