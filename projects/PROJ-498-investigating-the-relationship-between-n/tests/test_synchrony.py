import os
import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import mne
import tempfile
import shutil

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from synchrony import (
    get_region_for_electrode,
    get_pair_id,
    compute_wpli,
    compute_plv,
    compute_synchrony_metrics,
    save_synchrony_metrics
)

class TestSynchronyLogic(unittest.TestCase):
    
    def test_region_mapping(self):
        self.assertEqual(get_region_for_electrode('F3'), 'DLPFC')
        self.assertEqual(get_region_for_electrode('P4'), 'Parietal')
        self.assertIsNone(get_region_for_electrode('Cz'))

    def test_pair_id(self):
        self.assertEqual(get_pair_id(('F3', 'P4')), 'F3-P4')
        self.assertEqual(get_pair_id(('P4', 'F3')), 'F3-P4')

    def test_compute_wpli_constant_phase(self):
        """Test wPLI with constant phase difference (should be high)"""
        n_epochs = 10
        n_times = 1000
        sfreq = 1000
        
        # Create signals with constant phase difference
        t = np.linspace(0, 1, n_times)
        freq = 10
        phase_diff = np.pi / 4
        
        data1 = np.sin(2 * np.pi * freq * t).reshape(1, -1)
        data2 = np.sin(2 * np.pi * freq * t + phase_diff).reshape(1, -1)
        
        # Repeat for multiple epochs
        d1 = np.tile(data1, (n_epochs, 1))
        d2 = np.tile(data2, (n_epochs, 1))
        
        wpli = compute_wpli(d1, d2)
        # wPLI should be close to 1.0 for constant phase difference
        self.assertGreater(wpli, 0.8)

    def test_compute_wpli_random_phase(self):
        """Test wPLI with random phase difference (should be low)"""
        n_epochs = 100
        n_times = 1000
        
        # Random signals
        d1 = np.random.randn(n_epochs, n_times)
        d2 = np.random.randn(n_epochs, n_times)
        
        wpli = compute_wpli(d1, d2)
        # wPLI should be close to 0 for random phase
        self.assertLess(wpli, 0.2)

    def test_save_synchrony_metrics(self):
        """Test saving metrics to CSV"""
        metrics = {
            ('F3-P4', 'theta'): 0.5,
            ('F3-P4', 'gamma'): 0.3,
            ('F4-P3', 'theta'): 0.6
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_metrics.csv')
            save_synchrony_metrics(metrics, 'sub-01', output_path)
            
            self.assertTrue(os.path.exists(output_path))
            df = pd.read_csv(output_path)
            
            self.assertEqual(len(df), 3)
            self.assertIn('subject_id', df.columns)
            self.assertIn('pair_id', df.columns)
            self.assertIn('band', df.columns)
            self.assertIn('value', df.columns)
            
            self.assertEqual(df['subject_id'].iloc[0], 'sub-01')

class TestSynchronyIntegration(unittest.TestCase):
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.tmpdir, 'data', 'processed')
        self.metrics_dir = os.path.join(self.tmpdir, 'data', 'metrics')
        os.makedirs(self.data_dir)
        os.makedirs(self.metrics_dir)
        
        # Create a mock epoch file
        info = mne.create_info(ch_names=['F3', 'F4', 'P3', 'P4', 'Cz'], sfreq=500, ch_types='eeg')
        data = np.random.randn(5, 1000) # 5 channels, 2 seconds (1000 samples @ 500Hz)
        raw = mne.io.RawArray(data, info)
        
        events = np.array([[1000, 0, 1]]) # Stimulus at 1000 samples
        epochs = mne.Epochs(raw, events, tmin=-1.0, tmax=2.0, baseline=None, verbose=False)
        
        self.epochs_path = os.path.join(self.data_dir, 'sub-01_epochs.fif')
        epochs.save(self.epochs_path, overwrite=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_compute_synchrony_metrics_full(self):
        """Test end-to-end computation on mock data"""
        from synchrony import compute_synchrony_metrics
        
        epochs = mne.read_epochs(self.epochs_path, verbose=False)
        bands = {'theta': (4, 7), 'gamma': (30, 45)}
        
        metrics = compute_synchrony_metrics(epochs, bands, -1.0, 0.0)
        
        # Check that we got metrics for DLPFC-Parietal pairs
        expected_pairs = [('F3-P3', 'theta'), ('F3-P4', 'theta'), ('F4-P3', 'theta'), ('F4-P4', 'theta'),
                          ('F3-P3', 'gamma'), ('F3-P4', 'gamma'), ('F4-P3', 'gamma'), ('F4-P4', 'gamma')]
        
        for pair, band in expected_pairs:
            self.assertIn((pair, band), metrics)
            self.assertIsInstance(metrics[(pair, band)], float)

    def test_save_synchrony_metrics_integration(self):
        """Test saving to the expected output path"""
        from synchrony import main
        
        # Mock sys.argv to avoid argument parsing if needed, but main() takes no args
        # We need to patch the paths used in main()
        # Since main() uses hardcoded 'data/processed' and 'data/metrics', we change cwd
        
        original_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        
        try:
            main()
            
            output_csv = os.path.join(self.metrics_dir, 'synchrony_metrics.csv')
            self.assertTrue(os.path.exists(output_csv))
            
            df = pd.read_csv(output_csv)
            self.assertGreater(len(df), 0)
            self.assertEqual(df['subject_id'].iloc[0], 'sub-01')
        finally:
            os.chdir(original_cwd)

if __name__ == '__main__':
    unittest.main()