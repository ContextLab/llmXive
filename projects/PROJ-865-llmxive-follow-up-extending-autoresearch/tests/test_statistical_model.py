import json
import os
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import sys

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / 'code' / '04_analysis'))

from statistical_model import (
    load_results_csv,
    verify_paired_data_integrity,
    prepare_data_for_regression,
    fit_mixed_effects_model,
    extract_interaction_p_value,
    save_regression_results,
    generate_interaction_significance_report
)

class TestStatisticalModel(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, 'test_results.csv')
        
        # Create a mock dataset that satisfies the paired requirement
        # task_id, method, time_to_pivot, success, failure_type
        data = {
            'task_id': ['t1', 't1', 't2', 't2', 't3', 't3'],
            'method': ['baseline', 'rule_engine', 'baseline', 'rule_engine', 'baseline', 'rule_engine'],
            'time_to_pivot': [100.0, 80.0, 200.0, 150.0, 3600.0, 3600.0], # Last one censored
            'success': [1, 1, 0, 1, 0, 0],
            'failure_type': ['Syntactic Error', 'Syntactic Error', 'Semantic Ambiguity', 'Semantic Ambiguity', 'Logical Loop', 'Logical Loop']
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_csv, index=False)

    def tearDown(self):
        # Cleanup temp files
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

    def test_load_results_csv(self):
        df = load_results_csv(self.test_csv)
        self.assertEqual(len(df), 6)
        self.assertIn('task_id', df.columns)
        self.assertIn('method', df.columns)

    def test_verify_paired_data_integrity_valid(self):
        df = pd.read_csv(self.test_csv)
        is_valid, msg = verify_paired_data_integrity(df)
        self.assertTrue(is_valid)
        self.assertIsNone(msg)

    def test_verify_paired_data_integrity_invalid(self):
        # Create a CSV with missing pair
        bad_csv = os.path.join(self.temp_dir, 'bad_results.csv')
        bad_data = {
            'task_id': ['t1', 't1', 't2'],
            'method': ['baseline', 'rule_engine', 'baseline'],
            'time_to_pivot': [100, 80, 200],
            'success': [1, 1, 0],
            'failure_type': ['A', 'A', 'B']
        }
        pd.DataFrame(bad_data).to_csv(bad_csv, index=False)
        
        df = pd.read_csv(bad_csv)
        is_valid, msg = verify_paired_data_integrity(df)
        self.assertFalse(is_valid)
        self.assertIn('missing', msg.lower())

    def test_prepare_data_for_regression(self):
        df = load_results_csv(self.test_csv)
        prepared = prepare_data_for_regression(df)
        self.assertTrue(pd.api.types.is_categorical_dtype(prepared['failure_type']))
        self.assertTrue('is_censored' in prepared.columns)

    def test_fit_mixed_effects_model(self):
        df = load_results_csv(self.test_csv)
        # Ensure we have enough variance for the model to converge in a test environment
        # The mock data is very small, but statsmodels might handle it.
        # If it fails due to small sample size, we catch it.
        try:
            result = fit_mixed_effects_model(df)
            self.assertEqual(result['status'], 'success')
            self.assertIn('coefficients', result)
            self.assertIn('p_values', result)
        except Exception as e:
            # In a real environment with statsmodels, this should work.
            # If it fails here due to environment, we note it, but the code logic is correct.
            self.fail(f"Model fitting failed unexpectedly: {e}")

    def test_save_and_load_results(self):
        mock_results = {"status": "success", "coefficients": {"a": 1.0}}
        output_path = os.path.join(self.temp_dir, 'regression.json')
        save_regression_results(mock_results, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded['status'], 'success')

    def test_generate_interaction_report(self):
        mock_results = {
            "status": "success",
            "interaction_p_value": 0.03,
            "interaction_terms": ["failure_type[T.Semantic Ambiguity]:method[T.rule_engine]"],
            "converged": True,
            "formula": "test"
        }
        output_path = os.path.join(self.temp_dir, 'interaction_report.json')
        generate_interaction_significance_report(mock_results, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            report = json.load(f)
        self.assertTrue(report['is_significant'])
        self.assertEqual(report['conclusion'], 'Significant')

if __name__ == '__main__':
    unittest.main()