import os
import sys
import json
import hashlib
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_consistency_check import compute_file_hash, run_training_run, test_loso_consistency_across_runs
from utils.error_codes import ErrorCode

class TestCVConsistency(unittest.TestCase):

    def test_loso_consistency_across_runs(self):
        """
        Test that running the training pipeline multiple times with the same seed
        produces identical baseline comparison metrics.
        """
        # We will mock the run_training_pipeline to avoid actual heavy computation
        # but ensure the logic of comparison works.
        
        mock_metrics = {
            "null_model_mae": 10.5,
            "rf_model_mae": 8.2,
            "percentage_improvement": 21.9
        }

        with patch('scripts.run_consistency_check.run_training_pipeline') as mock_pipeline:
            with patch('scripts.run_consistency_check.open', create=True) as mock_open:
                # Mock the file read for baseline_comparison.json
                mock_file = MagicMock()
                mock_file.__enter__ = lambda s: mock_file
                mock_file.__exit__ = lambda s, *args: None
                mock_file.read = lambda: json.dumps(mock_metrics)
                mock_open.return_value = mock_file
                
                # Mock os.path.exists to return True
                with patch('scripts.run_consistency_check.os.path.exists', return_value=True):
                    with patch('scripts.run_consistency_check.log_info'):
                        with patch('scripts.run_consistency_check.log_error'):
                            success, message = test_loso_consistency_across_runs(num_runs=3)
                            
                            self.assertTrue(success, f"Test failed with message: {message}")
                            self.assertIn("Consistency verified", message)

    def test_compute_file_hash(self):
        """Test file hash computation."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = compute_file_hash(temp_path)
            hash2 = compute_file_hash(temp_path)
            self.assertEqual(hash1, hash2)
            self.assertEqual(len(hash1), 64) # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_run_training_run_failure(self):
        """Test that run_training_run handles failures gracefully."""
        with patch('scripts.run_consistency_check.run_training_pipeline', side_effect=Exception("Simulated Failure")):
            with patch('scripts.run_consistency_check.log_error'):
                with self.assertRaises(Exception):
                    run_training_run(42, 1, "data/artifacts")

if __name__ == '__main__':
    unittest.main()