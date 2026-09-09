"""
Unit tests for fetch_nrel_perovskites.py
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import csv
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from fetch_nrel_perovskites import filter_for_t_d, normalize_record, validate_checksum
from utils.checksum_verifier import compute_sha256

class TestFilterForTD(unittest.TestCase):
    
    def test_filter_with_tga_data(self):
        """Test filtering when TGA data is present."""
        materials = [
            {
                "formula": "MAPbI3",
                "experimental": [
                    {
                        "measurement_type": "TGA",
                        "property_name": "decomposition_temperature",
                        "value": 150.0,
                        "instrument_model": "TA Instruments",
                        "manufacturer": "TA Instruments",
                        "error": 2.0
                    }
                ]
            }
        ]
        
        result = filter_for_t_d(materials)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['formula'], 'MAPbI3')
        self.assertEqual(result[0]['T_d'], 150.0)
        self.assertEqual(result[0]['instrument_model'], 'TA Instruments')
        self.assertEqual(result[0]['temperature_precision'], 10.0) # Default from registry fallback or specific

    def test_filter_without_experimental(self):
        """Test filtering when no experimental data is present."""
        materials = [
            {
                "formula": "CsPbBr3",
                "experimental": []
            }
        ]
        
        result = filter_for_t_d(materials)
        self.assertEqual(len(result), 0)

    def test_filter_without_td_value(self):
        """Test filtering when experimental data exists but no T_d."""
        materials = [
            {
                "formula": "FAPbI3",
                "experimental": [
                    {
                        "measurement_type": "XRD",
                        "property_name": "lattice_parameter",
                        "value": 6.3
                    }
                ]
            }
        ]
        
        result = filter_for_t_d(materials)
        self.assertEqual(len(result), 0)

    def test_default_precision_for_unknown_instrument(self):
        """Test that default precision is used for unknown instruments."""
        materials = [
            {
                "formula": "MAPbBr3",
                "experimental": [
                    {
                        "measurement_type": "TGA",
                        "value": 140.0,
                        "instrument_model": "Unknown Model X",
                        "manufacturer": "Generic"
                    }
                ]
            }
        ]
        
        result = filter_for_t_d(materials)
        self.assertEqual(len(result), 1)
        # Should use default 10.0 as per T042/T052
        self.assertEqual(result[0]['temperature_precision'], 10.0)

class TestNormalizeRecord(unittest.TestCase):
    
    def test_normalize_structure(self):
        """Test that normalize_record produces correct keys."""
        record = {
            'formula': 'MAPbI3',
            'T_d': 150.0,
            'source': 'NREL',
            'instrument_model': 'TA',
            'manufacturer': 'TA',
            'temperature_precision': 10.0,
            'experimental_error': 2.0
        }
        
        normalized = normalize_record(record)
        
        expected_keys = ['formula', 'T_d', 'source', 'instrument_model', 
                       'manufacturer', 'temperature_precision', 'experimental_error']
        self.assertEqual(list(normalized.keys()), expected_keys)

class TestValidateChecksum(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = Path(self.temp_dir) / "test.csv"
        self.manifest_path = Path(self.temp_dir) / "checksum.json"
        
        # Create a dummy CSV
        with open(self.data_path, 'w') as f:
            f.write("formula,T_d\nMAPbI3,150\n")
        
        # Compute and save checksum
        checksum = compute_sha256(self.data_path)
        manifest = {'file': str(self.data_path), 'sha256': checksum}
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_valid_checksum(self):
        """Test validation passes when checksum matches."""
        self.assertTrue(validate_checksum(self.data_path, self.manifest_path))

    def test_invalid_checksum(self):
        """Test validation fails when checksum mismatches."""
        # Modify the data file
        with open(self.data_path, 'w') as f:
            f.write("formula,T_d\nCsPbI3,200\n")
        
        self.assertFalse(validate_checksum(self.data_path, self.manifest_path))

    def test_missing_manifest(self):
        """Test validation returns True (skips) if manifest is missing."""
        missing_manifest = Path(self.temp_dir) / "missing.json"
        self.assertTrue(validate_checksum(self.data_path, missing_manifest))

if __name__ == '__main__':
    unittest.main()