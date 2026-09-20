import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.models.null_baseline import (
    load_processed_data,
    compute_global_mean,
    predict_null_model,
    evaluate_model,
    compare_models,
    run_null_baseline_analysis
)

class TestNullBaseline(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = [
            {'temperature': 100.0, 'composition': 0.5, 'element_a': 'Cu', 'element_b': 'Zn'},
            {'temperature': 200.0, 'composition': 0.6, 'element_a': 'Cu', 'element_b': 'Zn'},
            {'temperature': 300.0, 'composition': 0.7, 'element_a': 'Al', 'element_b': 'Cu'},
            {'temperature': 400.0, 'composition': 0.8, 'element_a': 'Al', 'element_b': 'Cu'},
            {'temperature': 500.0, 'composition': 0.9, 'element_a': 'Cu', 'element_b': 'Zn'}
        ]
        
        # Create test CSV file
        self.test_csv_path = os.path.join(self.temp_dir, 'test_descriptors.csv')
        with open(self.test_csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['temperature', 'composition', 'element_a', 'element_b']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.test_data)
        
        # Create test LOSO results
        self.test_loso_path = os.path.join(self.temp_dir, 'test_loso_results.json')
        self.test_loso_data = {
            'aggregate': {
                'mae': 15.0,
                'r_squared': 0.85
            },
            'fold_results': [
                {'mae': 14.0, 'r_squared': 0.86},
                {'mae': 16.0, 'r_squared': 0.84}
            ]
        }
        with open(self.test_loso_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_loso_data, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_compute_global_mean(self):
        """Test that global mean is calculated correctly."""
        mean = compute_global_mean(self.test_data, target_column='temperature')
        expected_mean = (100 + 200 + 300 + 400 + 500) / 5
        self.assertAlmostEqual(mean, expected_mean, places=5)
    
    def test_predict_null_model(self):
        """Test that null model predicts global mean for all samples."""
        global_mean = 300.0
        predictions = predict_null_model(self.test_data, global_mean)
        self.assertEqual(len(predictions), len(self.test_data))
        self.assertTrue(all(p == global_mean for p in predictions))
    
    def test_evaluate_model_mae(self):
        """Test MAE calculation."""
        y_true = [100, 200, 300]
        y_pred = [110, 190, 310]
        metrics = evaluate_model(y_true, y_pred)
        expected_mae = (10 + 10 + 10) / 3
        self.assertAlmostEqual(metrics['mae'], expected_mae, places=5)
    
    def test_evaluate_model_r_squared(self):
        """Test R² calculation."""
        y_true = [100, 200, 300]
        y_pred = [100, 200, 300]  # Perfect prediction
        metrics = evaluate_model(y_true, y_pred)
        self.assertAlmostEqual(metrics['r_squared'], 1.0, places=5)
    
    def test_compare_models(self):
        """Test model comparison logic."""
        null_metrics = {'mae': 100.0, 'r_squared': 0.0}
        rf_metrics = {'mae': 50.0, 'r_squared': 0.8}
        
        comparison = compare_models(null_metrics, rf_metrics)
        
        self.assertAlmostEqual(comparison['null_model_mae'], 100.0, places=5)
        self.assertAlmostEqual(comparison['rf_model_mae'], 50.0, places=5)
        # Improvement should be 50%
        self.assertAlmostEqual(comparison['percentage_improvement'], 50.0, places=5)
    
    def test_run_null_baseline_analysis(self):
        """Test the full null baseline analysis pipeline."""
        output_path = os.path.join(self.temp_dir, 'baseline_comparison.json')
        
        result = run_null_baseline_analysis(
            processed_data_path=self.test_csv_path,
            loso_results_path=self.test_loso_path,
            output_path=output_path
        )
        
        # Verify output file exists
        self.assertTrue(os.path.exists(output_path))
        
        # Verify result structure
        self.assertIn('null_model_mae', result)
        self.assertIn('rf_model_mae', result)
        self.assertIn('percentage_improvement', result)
        
        # Verify RF MAE matches LOSO aggregate
        self.assertAlmostEqual(result['rf_model_mae'], 15.0, places=5)
        
        # Verify null MAE is calculated from data
        # Global mean = 300, predictions = [300, 300, 300, 300, 300]
        # MAE = (|100-300| + |200-300| + |300-300| + |400-300| + |500-300|) / 5 = 800/5 = 160
        self.assertAlmostEqual(result['null_model_mae'], 160.0, places=5)
        
        # Verify improvement calculation
        expected_improvement = ((160 - 15) / 160) * 100
        self.assertAlmostEqual(result['percentage_improvement'], expected_improvement, places=5)
    
    def test_run_null_baseline_analysis_file_not_found(self):
        """Test that appropriate error is raised when files are missing."""
        with self.assertRaises(FileNotFoundError):
            run_null_baseline_analysis(
                processed_data_path='nonexistent.csv',
                loso_results_path=self.test_loso_path,
                output_path=os.path.join(self.temp_dir, 'output.json')
            )

if __name__ == '__main__':
    import csv
    unittest.main()