"""
Unit tests for code/data/retrieval.py
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import csv
import tempfile
from pathlib import Path
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.retrieval import extract_records, write_raw_data

class TestExtraction(unittest.TestCase):

    def test_extract_records_valid(self):
        """Test extraction of valid Caco-2 measurement records."""
        mock_data = {
            "results": [
                {
                    "assay_chembl_id": "CHEMBL123",
                    "assay_type": "Caco-2",
                    "target_dictionary": {"target_chembl_id": "CHEMBL_TARGET"},
                    "documents": [
                        {
                            "standard_type": "MEASUREMENT",
                            "standard_value": 5.5,
                            "standard_units": "log cm/s",
                            "molecule_chembl_id": "CHEMBL_MOL",
                            "document_chembl_id": "DOC1"
                        }
                    ]
                }
            ]
        }
        
        # Mock the molecule fetch to return a SMILES
        with patch('data.retrieval.requests.get') as mock_get:
            # Mock response for molecule
            mol_resp = MagicMock()
            mol_resp.status_code = 200
            mol_resp.json.return_value = {
                "molecule_structures": [{"canonical_smiles": "CCO"}]
            }
            mock_get.return_value = mol_resp
            
            records = extract_records(mock_data)
            
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["assay_chembl_id"], "CHEMBL123")
            self.assertEqual(records[0]["logPapp"], 5.5)
            self.assertEqual(records[0]["smiles"], "CCO")

    def test_extract_records_invalid_type(self):
        """Test that non-Caco-2 assays are skipped."""
        mock_data = {
            "results": [
                {
                    "assay_chembl_id": "CHEMBL456",
                    "assay_type": "Binding",
                    "documents": []
                }
            ]
        }
        records = extract_records(mock_data)
        self.assertEqual(len(records), 0)

    def test_extract_records_null_value(self):
        """Test that records with null standard_value are skipped."""
        mock_data = {
            "results": [
                {
                    "assay_chembl_id": "CHEMBL789",
                    "assay_type": "Caco-2",
                    "documents": [
                        {
                            "standard_type": "MEASUREMENT",
                            "standard_value": None,
                            "molecule_chembl_id": "CHEMBL_MOL"
                        }
                    ]
                }
            ]
        }
        records = extract_records(mock_data)
        self.assertEqual(len(records), 0)

class TestWriting(unittest.TestCase):

    def test_write_raw_data(self):
        """Test writing records to CSV."""
        records = [
            {"assay_chembl_id": "A1", "target_chembl_id": "T1", "molecule_chembl_id": "M1", "smiles": "CC", "logPapp": 1.0, "units": "u", "document_chembl_id": "D1"},
            {"assay_chembl_id": "A2", "target_chembl_id": "T2", "molecule_chembl_id": "M2", "smiles": "CCO", "logPapp": 2.0, "units": "u", "document_chembl_id": "D2"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            write_raw_data(records, output_path)
            
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["smiles"], "CC")
            self.assertEqual(rows[1]["logPapp"], "2.0")

if __name__ == '__main__':
    unittest.main()