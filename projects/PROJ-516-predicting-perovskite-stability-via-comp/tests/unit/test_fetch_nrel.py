"""
Unit tests for fetch_nrel_perovskites.py
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from fetch_nrel_perovskites import filter_for_t_d, normalize_record, save_to_csv
import tempfile
import os

class TestFetchNREL(unittest.TestCase):

    def test_filter_for_t_d_valid(self):
        """Test filtering for valid T_d values."""
        materials = [
            {
                'formula': 'MAPbI3',
                'thermal_data': {'T_d': 500},
                'experimental_data': {}
            },
            {
                'formula': 'FAPbI3',
                'thermal_data': {'T_d': 400},
                'experimental_data': {}
            }
        ]
        result = filter_for_t_d(materials)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['formula'], 'MAPbI3')

    def test_filter_for_t_d_invalid(self):
        """Test filtering out invalid T_d values."""
        materials = [
            {
                'formula': 'FakePerovskite',
                'thermal_data': {'T_d': 50}, # Below threshold
                'experimental_data': {}
            },
            {
                'formula': 'NoTData',
                'thermal_data': {},
                'experimental_data': {}
            }
        ]
        result = filter_for_t_d(materials)
        self.assertEqual(len(result), 0)

    def test_normalize_record(self):
        """Test record normalization."""
        mat = {
            'id': 'nrel-123',
            'formula': 'CsPbBr3',
            'thermal_data': {'T_d': 600},
            'source_metadata': {
                'instrument_model': 'TA Instruments',
                'manufacturer': 'TA',
                'precision': 5
            }
        }
        norm = normalize_record(mat)
        self.assertEqual(norm['formula'], 'CsPbBr3')
        self.assertEqual(norm['T_d'], 600)
        self.assertEqual(norm['instrument_model'], 'TA Instruments')
        self.assertEqual(norm['source'], 'NREL')

    def test_save_to_csv(self):
        """Test saving records to CSV."""
        records = [
            {'formula': 'A', 'T_d': 100, 'instrument_model': 'X', 'manufacturer': 'Y', 'precision': 1, 'source': 'NREL', 'material_id': '1', 'raw_record': '{}'}
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'test.csv'
            save_to_csv(records, path)
            self.assertTrue(path.exists())
            with open(path, 'r') as f:
                content = f.read()
                self.assertIn('formula', content)
                self.assertIn('A', content)

if __name__ == '__main__':
    unittest.main()