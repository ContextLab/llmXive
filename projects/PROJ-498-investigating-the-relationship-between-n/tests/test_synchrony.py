"""
Tests for synchrony metrics computation.
"""
import os
import sys
import unittest
import tempfile
import numpy as np
import mne
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from synchrony import (
    get_region_for_electrode,
    get_all_electrode_pairs,
    get_cross_region_pairs,
    get_pair_id,
    compute_wpli,
    compute_plv,
    compute_synchrony_metrics,
    save_synchrony_metrics
)

class TestElectrodeMapping(unittest.TestCase):
    def test_region_mapping(self):
        self.assertEqual(get_region_for_electrode('F3'), 'DLPFC')
        self.assertEqual(get_region_for_electrode('P3'), 'Parietal')
        self.assertIsNone(get_region_for_electrode('O1'))

    def test_all_pairs(self):
        pairs = get_all_electrode_pairs()
        self.assertTrue(len(pairs) > 0)
        # Check a specific pair exists
        pair_ids = [get_pair_id(p[0], p[1]) for p in pairs]
        self.assertIn('F3-P3', pair_ids)

    def test_cross_region_pairs(self):
        pairs = get_cross_region_pairs()
        # Should contain DLPFC-Parietal pairs
        found = False
        for e1, e2 in pairs:
            r1 = get_region_for_electrode(e1)
            r2 = get_region_for_electrode(e2)
            if r1 != r2:
                found = True
                break
        self.assertTrue(found, "No cross-region pairs found")

class TestSynchronyMetrics(unittest.TestCase):
    def setUp(self):
        # Create a simple synthetic dataset for testing
        info = mne.create_info(ch_names=['F3', 'F4', 'P3', 'P4', 'EOG'], sfreq=250, ch_types='eeg')
        data = np.random.randn(10, 5, 500)  # 10 epochs, 5 channels, 500 time points
        epochs = mne.EpochsArray(data, info, tmin=-1.0)
        self.epochs = epochs

    def test_compute_wpli(self):
        # Test with random data
        pair_data = self.epochs.get_data()[:, [0, 2], :] # F3 and P3
        wpli = compute_wpli(pair_data)
        self.assertIsInstance(wpli, float)
        self.assertGreaterEqual(wpli, 0.0)
        self.assertLessEqual(wpli, 1.0)

    def test_compute_plv(self):
        pair_data = self.epochs.get_data()[:, [0, 2], :]
        plv = compute_plv(pair_data)
        self.assertIsInstance(plv, float)
        self.assertGreaterEqual(plv, 0.0)
        self.assertLessEqual(plv, 1.0)

    def test_compute_synchrony_metrics(self):
        # Add required electrode names to info if missing (mocking)
        # The test data has F3, F4, P3, P4
        metrics = compute_synchrony_metrics('test_sub', self.epochs, 'data/metrics')
        self.assertIsInstance(metrics, list)
        self.assertGreater(len(metrics), 0)
        
        # Check structure
        for m in metrics:
            self.assertIn('subject_id', m)
            self.assertIn('pair_id', m)
            self.assertIn('band', m)
            self.assertIn('value', m)
            self.assertIn(m['band'], ['theta', 'gamma'])

    def test_save_synchrony_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test.csv')
            results = [
                {'subject_id': '1', 'pair_id': 'F3-P3', 'band': 'theta', 'value': 0.5},
                {'subject_id': '1', 'pair_id': 'F3-P3', 'band': 'gamma', 'value': 0.3}
            ]
            save_synchrony_metrics(results, output_path)
            
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('subject_id', content)
                self.assertIn('F3-P3', content)

if __name__ == '__main__':
    unittest.main()