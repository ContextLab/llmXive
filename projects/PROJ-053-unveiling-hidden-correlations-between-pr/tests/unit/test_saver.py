import os
import sys
import tempfile
import pickle
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Mock the config to avoid path issues in unit tests
class MockConfig:
    @staticmethod
    def get_models_dir():
        return tempfile.gettempdir()
    
    @staticmethod
    def ensure_directories(paths):
        for p in paths:
            Path(p).mkdir(parents=True, exist_ok=True)

sys.modules['config'] = MockConfig

from models.saver import save_model, save_models

class TestSaver(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Patch the config function to return our temp dir
        with patch('models.saver.get_models_dir', return_value=self.temp_dir):
            pass # The patch is active during the test methods

    @patch('models.saver.get_models_dir')
    @patch('models.saver.ensure_directories')
    def test_save_model_creates_pickle_file(self, mock_ensure, mock_get_dir):
        mock_get_dir.return_value = self.temp_dir
        mock_ensure.return_value = None

        # Create a dummy model (simple object)
        dummy_model = {"param": "value", "weights": [1, 2, 3]}
        model_name = "test_model"

        result_path = save_model(dummy_model, model_name, "test")

        expected_path = os.path.join(self.temp_dir, f"{model_name}.pkl")
        self.assertEqual(result_path, expected_path)
        self.assertTrue(os.path.exists(expected_path))

        # Verify it can be loaded
        with open(expected_path, 'rb') as f:
            loaded_model = pickle.load(f)
        self.assertEqual(loaded_model, dummy_model)

    @patch('models.saver.get_models_dir')
    @patch('models.saver.ensure_directories')
    def test_save_model_raises_on_none(self, mock_ensure, mock_get_dir):
        mock_get_dir.return_value = self.temp_dir
        mock_ensure.return_value = None

        with self.assertRaises(FileNotFoundError):
            save_model(None, "null_model", "test")

    @patch('models.saver.get_models_dir')
    @patch('models.saver.ensure_directories')
    def test_save_models_saves_both(self, mock_ensure, mock_get_dir):
        mock_get_dir.return_value = self.temp_dir
        mock_ensure.return_value = None

        gpr_model = {"type": "gpr"}
        linear_model = {"type": "linear"}

        result = save_models(gpr_model, linear_model)

        self.assertIn("gpr_model_path", result)
        self.assertIn("linear_baseline_path", result)
        
        self.assertTrue(os.path.exists(result["gpr_model_path"]))
        self.assertTrue(os.path.exists(result["linear_baseline_path"]))

        # Verify content
        with open(result["gpr_model_path"], 'rb') as f:
            self.assertEqual(pickle.load(f), gpr_model)
        with open(result["linear_baseline_path"], 'rb') as f:
            self.assertEqual(pickle.load(f), linear_model)

if __name__ == '__main__':
    unittest.main()