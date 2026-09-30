import os
import tempfile
import pickle
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Import the function to test
from model_training import save_model, load_feature_matrix, train_random_forest

class TestModelSerialization(unittest.TestCase):

    def setUp(self):
        """Set up temporary directories and mock data for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.model_path = os.path.join(self.temp_dir.name, "test_model.pkl")
        
        # Create mock X and y for training a small model
        np.random.seed(42)
        self.X_mock = np.random.rand(100, 10)
        self.y_mock = np.random.randint(0, 2, 100)

    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()

    @patch('model_training.get_data_processed')
    def test_save_model_default_path(self, mock_get_processed):
        """Test that save_model writes to the default path when no path is provided."""
        mock_path = Path(self.temp_dir.name) / "processed"
        mock_path.mkdir(parents=True, exist_ok=True)
        mock_get_processed.return_value = mock_path
        
        # Train a small mock model
        model = train_random_forest(self.X_mock, self.y_mock, random_state=42)
        
        # Call save_model without explicit path
        save_model(model)
        
        expected_path = mock_path / "model.pkl"
        self.assertTrue(expected_path.exists(), f"Model not saved to default path: {expected_path}")

        # Verify the file is loadable
        with open(expected_path, 'rb') as f:
            loaded_model = pickle.load(f)
        
        self.assertIsNotNone(loaded_model)
        self.assertEqual(type(loaded_model), type(model))

    def test_save_model_custom_path(self):
        """Test that save_model writes to a specific custom path."""
        model = train_random_forest(self.X_mock, self.y_mock, random_state=42)
        
        save_model(model, self.model_path)
        
        self.assertTrue(os.path.exists(self.model_path), f"Model not saved to custom path: {self.model_path}")
        
        # Verify content
        with open(self.model_path, 'rb') as f:
            loaded_model = pickle.load(f)
        
        self.assertIsNotNone(loaded_model)

    def test_save_model_creates_directory(self):
        """Test that save_model creates the parent directory if it doesn't exist."""
        nested_path = os.path.join(self.temp_dir.name, "deep", "nested", "model.pkl")
        
        model = train_random_forest(self.X_mock, self.y_mock, random_state=42)
        save_model(model, nested_path)
        
        self.assertTrue(os.path.exists(nested_path))

    def test_model_predict_after_load(self):
        """Test that the loaded model can make predictions."""
        model = train_random_forest(self.X_mock, self.y_mock, random_state=42)
        save_model(model, self.model_path)
        
        with open(self.model_path, 'rb') as f:
            loaded_model = pickle.load(f)
        
        # Make prediction
        pred = loaded_model.predict(self.X_mock[:5])
        self.assertEqual(len(pred), 5)
        self.assertTrue(all(p in [0, 1] for p in pred))

if __name__ == '__main__':
    unittest.main()