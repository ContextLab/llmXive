import os
import sys
import json
import tempfile
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from train import load_variable_peaks, run_cross_validation, train_elastic_net

class TestTrainElasticNet(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.temp_dir.name, "test_imputed.csv")
        
        # Create a mock input file
        # Structure: Gene_ID, CellLine_Peak1, CellLine_Peak2, CellLine_Expression
        data = {
            'Gene_ID': ['Gene1', 'Gene2', 'Gene3', 'Gene4', 'Gene5'],
            'GM12878_peak_1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'GM12878_peak_2': [2.0, 3.0, 4.0, 5.0, 6.0],
            'GM12878_expression': [10.0, 20.0, 30.0, 40.0, 50.0],
            'K562_peak_1': [1.5, 2.5, 3.5, 4.5, 5.5],
            'K562_peak_2': [2.5, 3.5, 4.5, 5.5, 6.5],
            'K562_expression': [15.0, 25.0, 35.0, 45.0, 55.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.input_path, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_variable_peaks_splits_cell_lines(self):
        gene_ids, cell_line_features = load_variable_peaks(self.input_path)
        
        self.assertIn('GM12878', cell_line_features)
        self.assertIn('K562', cell_line_features)
        
        gm12878_df = cell_line_features['GM12878']
        self.assertIn('GM12878_peak_1', gm12878_df.columns)
        self.assertIn('GM12878_peak_2', gm12878_df.columns)
        self.assertIn('GM12878_expression', gm12878_df.columns)
        
        self.assertEqual(len(gene_ids), 5)

    def test_run_cross_validation(self):
        # Create simple numpy arrays
        X = np.random.rand(100, 10)
        y = np.random.rand(100)
        
        results = run_cross_validation(X, y)
        
        self.assertIn('mean_scores', results)
        self.assertIn('best_alpha', results)
        self.assertIn('mean_cv_score', results)
        self.assertIsInstance(results['mean_scores'], list)
        self.assertGreater(len(results['mean_scores']), 0)

    def test_train_elastic_net(self):
        X = np.random.rand(50, 5)
        y = np.random.rand(50)
        
        model = train_elastic_net(X, y)
        
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'coef_'))
        self.assertTrue(hasattr(model, 'intercept_'))

if __name__ == '__main__':
    unittest.main()