"""
Unit tests for the Elastic Net training module.
"""
import os
import sys
import tempfile
import json
import pickle
import unittest
import numpy as np
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.train import train_elastic_net, run_training_for_cell_line
from code.utils import load_config

class TestElasticNetTraining(unittest.TestCase):
    
    def setUp(self):
        # Create a simple synthetic dataset for testing
        np.random.seed(42)
        n_samples = 100
        n_features = 50
        
        # Generate features
        X = np.random.randn(n_samples, n_features)
        # Generate target with some linear relationship
        true_coef = np.random.randn(n_features)
        y = X @ true_coef + np.random.randn(n_samples) * 0.1
        
        self.X = X
        self.y = y
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp files if any
        pass

    def test_train_elastic_net_basic(self):
        """Test basic training of Elastic Net."""
        model, cv_results, scaler = train_elastic_net(self.X, self.y, alpha=0.5, cv_folds=3)
        
        self.assertIsNotNone(model)
        self.assertEqual(model.l1_ratio, 0.5)
        self.assertIn("best_alpha", cv_results)
        self.assertIn("best_score", cv_results)
        self.assertIsNotNone(scaler)
        
        # Check that model can predict
        predictions = model.predict(self.X)
        self.assertEqual(predictions.shape, self.y.shape)

    def test_run_training_for_cell_line(self):
        """Test the full training pipeline for a cell line."""
        # Create a dummy input CSV
        df = pd.DataFrame({
            'gene': [f'gene_{i}' for i in range(100)],
            'cell_line': ['GM12878'] * 100,
            'expression': np.random.randn(100),
            **{f'peak_{i}': np.random.randn(100) for i in range(20)}
        })
        
        input_path = os.path.join(self.temp_dir, 'test_variable_peaks.csv')
        df.to_csv(input_path, index=False)
        
        model_path = os.path.join(self.temp_dir, 'test_model.pkl')
        score_path = os.path.join(self.temp_dir, 'test_scores.json')
        
        success = run_training_for_cell_line(
            'GM12878', input_path, model_path, score_path
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(model_path))
        self.assertTrue(os.path.exists(score_path))
        
        # Check model content
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        self.assertIn('model', model_data)
        self.assertIn('scaler', model_data)
        self.assertEqual(model_data['cell_line'], 'GM12878')
        
        # Check scores content
        with open(score_path, 'r') as f:
            scores = json.load(f)
        self.assertIn('best_alpha', scores)
        self.assertEqual(scores['cell_line'], 'GM12878')

if __name__ == '__main__':
    unittest.main()