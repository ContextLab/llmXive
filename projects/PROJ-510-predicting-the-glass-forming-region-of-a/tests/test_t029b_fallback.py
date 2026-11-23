"""
Tests for T029b Stable Model Fallback.
"""
import os
import sys
import json
import pickle
import tempfile
import shutil
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from t029b_fallback import ensure_stable_model_exists, run_fallback

class TestT029bFallback(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.models_dir = os.path.join(self.temp_dir, "data", "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Create a dummy baseline model
        self.baseline_path = os.path.join(self.models_dir, "random_forest_model.pkl")
        with open(self.baseline_path, 'wb') as f:
            pickle.dump({"model_type": "baseline"}, f)
        
        self.stable_path = os.path.join(self.models_dir, "random_forest_model_stable.pkl")
        
        # Patch the constants in the module
        self.patcher = patch('t029b_fallback.MODELS_DIR', self.models_dir)
        self.patcher.start()
        self.patcher_baseline = patch('t029b_fallback.BASELINE_MODEL', "random_forest_model.pkl")
        self.patcher_baseline.start()
        self.patcher_stable = patch('t029b_fallback.STABLE_MODEL', "random_forest_model_stable.pkl")
        self.patcher_stable.start()

    def tearDown(self):
        """Clean up temporary directory."""
        self.patcher.stop()
        self.patcher_baseline.stop()
        self.patcher_stable.stop()
        shutil.rmtree(self.temp_dir)

    def test_stable_model_already_exists(self):
        """Test that if stable model exists, it is not overwritten."""
        # Create stable model
        with open(self.stable_path, 'wb') as f:
            pickle.dump({"model_type": "stable"}, f)
        
        result = ensure_stable_model_exists()
        
        self.assertEqual(result, self.stable_path)
        # Verify content is still stable
        with open(self.stable_path, 'rb') as f:
            data = pickle.load(f)
        self.assertEqual(data['model_type'], 'stable')

    def test_fallback_copies_baseline(self):
        """Test that if stable model is missing, baseline is copied."""
        # Ensure stable model does NOT exist
        if os.path.exists(self.stable_path):
            os.remove(self.stable_path)
        
        result = ensure_stable_model_exists()
        
        self.assertEqual(result, self.stable_path)
        self.assertTrue(os.path.exists(self.stable_path))
        
        # Verify content matches baseline
        with open(self.stable_path, 'rb') as f:
            data = pickle.load(f)
        self.assertEqual(data['model_type'], 'baseline')

    def test_fails_if_neither_exists(self):
        """Test that FileNotFoundError is raised if both models are missing."""
        os.remove(self.baseline_path)
        if os.path.exists(self.stable_path):
            os.remove(self.stable_path)
        
        with self.assertRaises(FileNotFoundError):
            ensure_stable_model_exists()

    def test_run_fallback_success(self):
        """Test the CLI entry point when fallback is successful."""
        # Ensure stable model does NOT exist
        if os.path.exists(self.stable_path):
            os.remove(self.stable_path)
        
        exit_code = run_fallback()
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(self.stable_path))

    def test_run_fallback_fail(self):
        """Test the CLI entry point when baseline is missing."""
        os.remove(self.baseline_path)
        if os.path.exists(self.stable_path):
            os.remove(self.stable_path)
        
        exit_code = run_fallback()
        self.assertEqual(exit_code, 1)

if __name__ == '__main__':
    unittest.main()