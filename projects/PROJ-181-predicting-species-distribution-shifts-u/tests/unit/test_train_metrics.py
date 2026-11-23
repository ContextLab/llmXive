"""
Unit tests for code/train_metrics.py (Task T026)
"""
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

# Mock the project config and logger to avoid dependency issues in tests
import sys
from io import StringIO

class TestTrainMetrics(unittest.TestCase):

    def test_calculate_auc_tss(self):
        """Test the AUC and TSS calculation function."""
        from code.train_metrics import calculate_auc_tss
        
        # Perfect prediction
        y_true = np.array([1, 1, 0, 0])
        y_proba = np.array([0.9, 0.8, 0.2, 0.1])
        y_pred = np.array([1, 1, 0, 0])
        
        auc, tss = calculate_auc_tss(y_true, y_proba, y_pred)
        
        self.assertEqual(auc, 1.0)
        self.assertEqual(tss, 1.0)

    def test_calculate_auc_tss_random(self):
        """Test AUC and TSS with random predictions."""
        from code.train_metrics import calculate_auc_tss
        
        y_true = np.array([1, 1, 0, 0, 1, 0])
        y_proba = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        y_pred = np.array([0, 0, 0, 0, 0, 0])
        
        # AUC for random is 0.5
        auc, tss = calculate_auc_tss(y_true, y_proba, y_pred)
        
        self.assertAlmostEqual(auc, 0.5, places=1)
        # TSS should be low (specificity 1, sensitivity 0 -> TSS 0)
        self.assertAlmostEqual(tss, 0.0, places=1)

    @patch('code.train_metrics.load_clean_data')
    @patch('code.train_metrics.load_model')
    @patch('code.train_metrics.prepare_features_and_labels')
    @patch('code.train_metrics.predict_model')
    @patch('code.train_metrics.calculate_auc_tss')
    @patch('pandas.DataFrame.to_csv')
    def test_run_metrics_calculation_integration(self, mock_to_csv, mock_calc, mock_pred, mock_prep, mock_load_model, mock_load_data):
        """Integration test for the main calculation flow."""
        from code.train_metrics import run_metrics_calculation
        
        # Mock data
        mock_df = pd.DataFrame({'species': ['sp1', 'sp2'], 'presence': [1, 0]})
        mock_load_data.return_value = mock_df
        
        mock_prep.return_value = (np.array([[1, 2]]), np.array([1]), np.array([[3, 4]]), np.array([0]), ['bio1', 'bio2'])
        
        mock_load_model.return_value = MagicMock()
        mock_pred.return_value = (np.array([0.9]), np.array([1]))
        mock_calc.return_value = (0.9, 0.8)
        
        # Run
        run_metrics_calculation()
        
        # Verify to_csv was called
        mock_to_csv.assert_called_once()

if __name__ == '__main__':
    unittest.main()