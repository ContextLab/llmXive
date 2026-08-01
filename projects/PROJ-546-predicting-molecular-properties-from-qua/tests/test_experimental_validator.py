"""
Unit tests for the experimental validator module.
"""
import csv
import json
import os
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from evaluators.experimental_validator import (
    load_experimental_data,
    load_predictions,
    align_data,
    calculate_error_margin,
    verify_standard_of_evidence,
    generate_validation_report
)
from utils.validation_utils import ValidationError

class TestExperimentalValidator(unittest.TestCase):
    
    def setUp(self):
        """Create temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.exp_csv = os.path.join(self.temp_dir, 'experimental.csv')
        self.pred_csv = os.path.join(self.temp_dir, 'predictions.csv')
        self.report_json = os.path.join(self.temp_dir, 'validation_report.json')
        
        # Create sample experimental data
        with open(self.exp_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['smiles', 'experimental_barrier', 'net_charge'])
            writer.writeheader()
            writer.writerows([
                {'smiles': 'CCO', 'experimental_barrier': 10.5, 'net_charge': 0},
                {'smiles': 'CCCO', 'experimental_barrier': 12.3, 'net_charge': 0},
                {'smiles': 'CCCCO', 'experimental_barrier': 14.1, 'net_charge': 0},
                {'smiles': 'CC(C)O', 'experimental_barrier': 11.2, 'net_charge': 0},
                {'smiles': 'CC=O', 'experimental_barrier': 8.9, 'net_charge': 0},
            ])
        
        # Create sample predictions
        with open(self.pred_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['smiles', 'predicted_barrier', 'experimental_barrier'])
            writer.writeheader()
            writer.writerows([
                {'smiles': 'CCO', 'predicted_barrier': 10.8, 'experimental_barrier': 10.5},
                {'smiles': 'CCCO', 'predicted_barrier': 12.1, 'experimental_barrier': 12.3},
                {'smiles': 'CCCCO', 'predicted_barrier': 14.5, 'experimental_barrier': 14.1},
                {'smiles': 'CC(C)O', 'predicted_barrier': 11.0, 'experimental_barrier': 11.2},
                {'smiles': 'CC=O', 'predicted_barrier': 9.2, 'experimental_barrier': 8.9},
            ])
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_experimental_data(self):
        """Test loading experimental data from CSV."""
        data = load_experimental_data(self.exp_csv)
        self.assertEqual(len(data), 5)
        self.assertIn('smiles', data[0])
        self.assertIn('experimental_barrier', data[0])
        self.assertIsInstance(data[0]['experimental_barrier'], float)
    
    def test_load_predictions(self):
        """Test loading predictions from CSV."""
        data = load_predictions(self.pred_csv)
        self.assertEqual(len(data), 5)
        self.assertIn('smiles', data[0])
        self.assertIn('predicted_barrier', data[0])
        self.assertIsInstance(data[0]['predicted_barrier'], float)
    
    def test_align_data(self):
        """Test aligning experimental and prediction data."""
        exp_data = load_experimental_data(self.exp_csv)
        pred_data = load_predictions(self.pred_csv)
        
        aligned_exp, aligned_pred = align_data(exp_data, pred_data)
        
        self.assertEqual(len(aligned_exp), 5)
        self.assertEqual(len(aligned_pred), 5)
        self.assertEqual(aligned_exp[0]['smiles'], aligned_pred[0]['smiles'])
    
    def test_align_data_missing(self):
        """Test alignment with missing predictions."""
        # Create predictions with a missing entry
        with open(self.pred_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['smiles', 'predicted_barrier'])
            writer.writeheader()
            writer.writerows([
                {'smiles': 'CCO', 'predicted_barrier': 10.8},
                {'smiles': 'CCCO', 'predicted_barrier': 12.1},
                # Missing: CCCCO, CC(C)O, CC=O
            ])
        
        exp_data = load_experimental_data(self.exp_csv)
        pred_data = load_predictions(self.pred_csv)
        
        aligned_exp, aligned_pred = align_data(exp_data, pred_data)
        
        self.assertEqual(len(aligned_exp), 2)
        self.assertEqual(len(aligned_pred), 2)
    
    def test_calculate_error_margin(self):
        """Test error margin calculation."""
        exp_data = load_experimental_data(self.exp_csv)
        pred_data = load_predictions(self.pred_csv)
        
        aligned_exp, aligned_pred = align_data(exp_data, pred_data)
        metrics = calculate_error_margin(aligned_pred, aligned_exp)
        
        self.assertIn('mae_kcal_mol', metrics)
        self.assertIn('rmse_kcal_mol', metrics)
        self.assertIn('max_error_kcal_mol', metrics)
        self.assertIn('n_samples', metrics)
        self.assertEqual(metrics['n_samples'], 5)
        
        # Verify MAE calculation (manual check)
        # Errors: |10.8-10.5|=0.3, |12.1-12.3|=0.2, |14.5-14.1|=0.4, |11.0-11.2|=0.2, |9.2-8.9|=0.3
        # Sum = 1.4, MAE = 1.4/5 = 0.28
        self.assertAlmostEqual(metrics['mae_kcal_mol'], 0.28, places=2)
    
    def test_calculate_error_margin_empty(self):
        """Test error margin calculation with no data."""
        with self.assertRaises(ValueError):
            calculate_error_margin([], [])
    
    def test_verify_standard_of_evidence_pass(self):
        """Test verification when metrics pass."""
        metrics = {
            'mae_kcal_mol': 1.5,
            'n_samples': 50,
            'rmse_kcal_mol': 2.0,
            'max_error_kcal_mol': 3.0
        }
        
        result = verify_standard_of_evidence(metrics)
        
        self.assertEqual(result['status'], 'pass')
        self.assertIn('MAE', str(result['details']))
    
    def test_verify_standard_of_evidence_fail_mae(self):
        """Test verification when MAE exceeds threshold."""
        metrics = {
            'mae_kcal_mol': 2.5,  # Exceeds 2.0
            'n_samples': 50,
            'rmse_kcal_mol': 3.0,
            'max_error_kcal_mol': 4.0
        }
        
        result = verify_standard_of_evidence(metrics)
        
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any('exceeds' in d for d in result['details']))
    
    def test_verify_standard_of_evidence_fail_samples(self):
        """Test verification when sample size is too low."""
        metrics = {
            'mae_kcal_mol': 1.0,
            'n_samples': 10,  # Below 30
            'rmse_kcal_mol': 1.5,
            'max_error_kcal_mol': 2.0
        }
        
        result = verify_standard_of_evidence(metrics)
        
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any('below minimum' in d for d in result['details']))
    
    def test_generate_validation_report(self):
        """Test full validation report generation."""
        exp_data = load_experimental_data(self.exp_csv)
        pred_data = load_predictions(self.pred_csv)
        
        report = generate_validation_report(exp_data, pred_data, self.report_json)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.report_json))
        
        # Verify report structure
        self.assertIn('standard_of_evidence', report)
        self.assertIn('alignment', report)
        self.assertIn('error_margin', report)
        self.assertIn('verification', report)
        
        # Verify JSON content
        with open(self.report_json, 'r') as f:
            loaded_report = json.load(f)
        
        self.assertEqual(report, loaded_report)

if __name__ == '__main__':
    unittest.main()