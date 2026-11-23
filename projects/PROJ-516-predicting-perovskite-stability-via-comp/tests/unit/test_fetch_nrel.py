"""
Unit tests for NREL data fetching (T012a).
"""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import csv
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from fetch_nrel_perovskites import (
    fetch_nrel_materials,
    filter_for_t_d,
    normalize_record,
    save_to_csv,
    validate_checksum
)

class TestNRELFetcher(unittest.TestCase):

    def test_filter_for_t_d(self):
        """Test filtering for T_d data."""
        records = [
            {"formula": "CsPbI3", "thermal_properties": {"T_d": 450}},
            {"formula": "FAPbI3", "thermal_properties": {"other": 100}},
            {"formula": "MAPbBr3", "thermal_properties": {"T_d": 380}}
        ]

        filtered = filter_for_t_d(records)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["formula"], "CsPbI3")
        self.assertEqual(filtered[1]["formula"], "MAPbBr3")

    def test_normalize_record(self):
        """Test record normalization."""
        raw_record = {
            "formula": "CsPbI3",
            "material_id": "nrel-123",
            "thermal_properties": {"T_d": 450},
            "instrumentation": {
                "model": "TA Q500",
                "manufacturer": "TA Instruments",
                "precision_celsius": 5.0
            }
        }

        normalized = normalize_record(raw_record)

        self.assertEqual(normalized["formula"], "CsPbI3")
        self.assertEqual(normalized["T_d"], 450)
        self.assertEqual(normalized["source"], "NREL")
        self.assertEqual(normalized["instrument_model"], "TA Q500")
        self.assertEqual(normalized["manufacturer"], "TA Instruments")
        self.assertEqual(normalized["precision_celsius"], 5.0)

    def test_normalize_record_missing_instrumentation(self):
        """Test normalization with missing instrumentation data."""
        raw_record = {
            "formula": "CsPbI3",
            "material_id": "nrel-123",
            "thermal_properties": {"T_d": 450}
        }

        normalized = normalize_record(raw_record)

        self.assertEqual(normalized["instrument_model"], "Unknown")
        self.assertEqual(normalized["manufacturer"], "Unknown")
        self.assertEqual(normalized["precision_celsius"], 10.0)

    def test_save_to_csv(self, tmp_path):
        """Test saving records to CSV."""
        records = [
            {"formula": "CsPbI3", "T_d": 450, "source": "NREL",
             "instrument_model": "TA Q500", "manufacturer": "TA Instruments",
             "precision_celsius": 5.0, "material_id": "nrel-123"}
        ]

        output_path = tmp_path / "test_output.csv"
        save_to_csv(records, output_path)

        self.assertTrue(output_path.exists())

        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["formula"], "CsPbI3")
        self.assertEqual(rows[0]["T_d"], "450")

    @patch('fetch_nrel_perovskites.fetch_with_retry')
    @patch('fetch_nrel_perovskites.load_config')
    def test_fetch_nrel_materials_success(self, mock_load_config, mock_fetch):
        """Test successful fetch from NREL API."""
        mock_config = {"api_key": "test-key"}
        mock_load_config.return_value = mock_config

        mock_response = {
            "results": [
                {"formula": "CsPbI3", "material_id": "1", "thermal_properties": {"T_d": 450}},
                {"formula": "FAPbI3", "material_id": "2", "thermal_properties": {"T_d": 380}}
            ]
        }
        mock_fetch.return_value = mock_response

        # Set environment variable
        import os
        os.environ["NREL_API_KEY"] = "test-key"

        try:
            data = fetch_nrel_materials()
            self.assertEqual(len(data), 2)
        finally:
            del os.environ["NREL_API_KEY"]

    def test_validate_checksum(self, tmp_path):
        """Test checksum validation."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Create a manifest with correct checksum
        import hashlib
        checksum = hashlib.sha256(b"Hello, World!").hexdigest()
        manifest = {"sha256": checksum}
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))

        # Validate
        self.assertTrue(validate_checksum(test_file, manifest_path))

    def test_validate_checksum_mismatch(self, tmp_path):
        """Test checksum validation with mismatch."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Create a manifest with wrong checksum
        manifest = {"sha256": "wrong_checksum"}
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))

        # Validate - should return False
        self.assertFalse(validate_checksum(test_file, manifest_path))

if __name__ == "__main__":
    unittest.main()