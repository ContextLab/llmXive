"""
Unit tests for sensitivity_analysis.py.

Tests:
    - extract_feature_importance
    - identify_top_descriptors
    - run_sensitivity_sweep (mocked)
    - generate_summary_report
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Import the module functions
from code.sensitivity_analysis import (
    extract_feature_importance,
    identify_top_descriptors,
    run_sensitivity_sweep,
    generate_summary_report
)

class TestFeatureImportance(unittest.TestCase):
    
    def test_extract_feature_importance(self):
        """Test extraction of feature importance."""
        # Mock model with feature_importances_
        mock_model = MagicMock()
        mock_model.feature_importances_ = np.array([0.1, 0.5, 0.2, 0.2])
        feature_names = ["A", "B", "C", "D"]
        
        result = extract_feature_importance(mock_model, feature_names)
        
        self.assertEqual(len(result), 4)
        # Should be sorted by importance descending
        self.assertEqual(result[0]["feature"], "B")
        self.assertEqual(result[0]["importance"], 0.5)
        self.assertEqual(result[0]["rank"], 1)
        
    def test_extract_feature_importance_no_attr(self):
        """Test error when model lacks feature_importances_."""
        mock_model = MagicMock(spec=[])
        feature_names = ["A"]
        
        with self.assertRaises(AttributeError):
            extract_feature_importance(mock_model, feature_names)
            
    def test_identify_top_descriptors(self):
        """Test identification of top N descriptors."""
        importance_list = [
            {"feature": "A", "importance": 0.1},
            {"feature": "B", "importance": 0.5},
            {"feature": "C", "importance": 0.2},
            {"feature": "D", "importance": 0.2}
        ]
        
        top_2 = identify_top_descriptors(importance_list, n_top=2)
        
        self.assertEqual(len(top_2), 2)
        self.assertEqual(top_2[0]["feature"], "B")
        self.assertEqual(top_2[0]["cumulative_importance"], 0.5)
        self.assertEqual(top_2[1]["cumulative_importance"], 0.7)
        
class TestSensitivitySweep(unittest.TestCase):
    
    @patch('code.sensitivity_analysis.RandomForestRegressor')
    @patch('code.sensitivity_analysis.cross_val_score')
    def test_run_sensitivity_sweep(self, mock_cv, mock_rf):
        """Test the sensitivity sweep logic."""
        # Setup mocks
        mock_rf_instance = MagicMock()
        mock_rf.return_value = mock_rf_instance
        mock_cv.return_value = np.array([-1.0, -1.2, -0.9]) # neg_mae
        
        mock_model = MagicMock()
        mock_model.get_params.return_value = {'n_estimators': 10}
        
        X = np.random.rand(20, 4)
        y = np.random.rand(20)
        feature_names = ["A", "B", "C", "D"]
        importance_list = [
            {"feature": "B", "importance": 0.5},
            {"feature": "C", "importance": 0.2},
            {"feature": "D", "importance": 0.2},
            {"feature": "A", "importance": 0.1}
        ]
        
        result = run_sensitivity_sweep(
            mock_model, X, y, feature_names, importance_list, percentiles=[50]
        )
        
        self.assertIn("sweep_results", result)
        self.assertEqual(len(result["sweep_results"]), 1)
        self.assertEqual(result["sweep_results"][0]["n_features"], 2)
        self.assertIn("B", result["sweep_results"][0]["features_used"])
        
class TestReportGeneration(unittest.TestCase):
    
    def test_generate_summary_report(self):
        """Test markdown report generation."""
        top_desc = [
            {"feature": "HOMO", "importance": 0.5, "cumulative_importance": 0.5},
            {"feature": "LUMO", "importance": 0.3, "cumulative_importance": 0.8}
        ]
        
        sweep_res = {
            "sweep_results": [
                {"percentile": 50, "n_features": 2, "mean_mae": 1.2, "std_mae": 0.1, "status": "success"},
                {"percentile": 20, "n_features": 1, "mean_mae": 2.5, "std_mae": 0.5, "status": "success"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = f.name
            
        try:
            generate_summary_report(top_desc, sweep_res, temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                
            self.assertIn("# Sensitivity Analysis Report", content)
            self.assertIn("Top 5 Descriptors", content)
            self.assertIn("HOMO", content)
            self.assertIn("LUMO", content)
            self.assertIn("| 50% | 2 |", content)
            self.assertIn("## Conclusion", content)
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()