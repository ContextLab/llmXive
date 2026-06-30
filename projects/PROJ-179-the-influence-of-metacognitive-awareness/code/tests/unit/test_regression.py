import os
import sys
import json
import tempfile
import unittest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.regression import compute_d_prime, compute_type2_auc, run_regression_analysis

class TestRegressionHelpers(unittest.TestCase):
    
    def test_compute_d_prime(self):
        # Create mock data
        data = {
            'source_label': [1, 1, 1, 0, 0, 0],
            'participant_response': [1, 1, 0, 0, 0, 1] # Hits: 2/3, FA: 1/3
        }
        df = pd.DataFrame(data)
        d_prime = compute_d_prime(df)
        self.assertFalse(np.isnan(d_prime))
        self.assertGreater(d_prime, 0) # Should be positive given more hits than FAs
    
    def test_compute_type2_auc(self):
        # Create mock data where confidence is higher for correct answers
        data = {
            'accuracy': [1, 1, 1, 0, 0, 0],
            'confidence_rating': [0.9, 0.95, 0.85, 0.2, 0.3, 0.1]
        }
        df = pd.DataFrame(data)
        auc = compute_type2_auc(df)
        self.assertGreater(auc, 0.5) # Should be > 0.5 if metacognition is good
    
    def test_run_regression_analysis_with_working_memory(self):
        # Mock participant data
        data = {
            'participant_id': [1, 2, 3, 4, 5],
            'metacognitive_score': [0.8, 0.6, 0.9, 0.5, 0.7],
            'reality_testing_accuracy': [2.1, 1.5, 2.3, 1.2, 1.8],
            'age': [20, 25, 30, 22, 28],
            'gender': ['M', 'F', 'M', 'F', 'M'],
            'working_memory': [50, 55, 60, 48, 52]
        }
        df = pd.DataFrame(data)
        results = run_regression_analysis(df)
        
        self.assertIn('step_1', results)
        self.assertIn('step_2', results)
        self.assertIn('change_statistics', results)
        self.assertIn('working_memory_present', results)
        self.assertTrue(results['working_memory_present'])
        self.assertFalse(results['n_minus_1_model'])
    
    def test_run_regression_analysis_without_working_memory(self):
        # Mock participant data WITHOUT working memory
        data = {
            'participant_id': [1, 2, 3, 4, 5],
            'metacognitive_score': [0.8, 0.6, 0.9, 0.5, 0.7],
            'reality_testing_accuracy': [2.1, 1.5, 2.3, 1.2, 1.8],
            'age': [20, 25, 30, 22, 28],
            'gender': ['M', 'F', 'M', 'F', 'M']
            # No working_memory
        }
        df = pd.DataFrame(data)
        results = run_regression_analysis(df)
        
        self.assertIn('change_statistics', results)
        self.assertFalse(results['working_memory_present'])
        self.assertTrue(results['n_minus_1_model'])
        self.assertIn('adj_r_squared', results['step_2'])

if __name__ == '__main__':
    unittest.main()