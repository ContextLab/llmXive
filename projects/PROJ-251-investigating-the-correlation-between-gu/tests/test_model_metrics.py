import unittest
import json
import os
import tempfile
from pathlib import Path
from code.utils.validators import validate_model_metrics_schema

class TestModelMetricsFormat(unittest.TestCase):
    """Test suite for model metrics validation and format."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_metrics = {
            'mean_accuracy': 0.65,
            'std_accuracy': 0.05,
            'mean_precision': 0.64,
            'mean_recall': 0.66,
            'mean_f1_score': 0.65,
            'meets_accuracy_target': True,
            'accuracy_target': 0.60,
            'significance_pvalue': 0.03,
            'significant_taxa_count': 5,
            'total_thresholds_evaluated': 3,
            'use_synthetic_data': False,
            'seroconversion_threshold': 4.0,
            'threshold_details': [
                {'threshold': 4.0, 'accuracy': 0.65, 'precision': 0.64, 'recall': 0.66, 'f1_score': 0.65},
                {'threshold': 4.4, 'accuracy': 0.63, 'precision': 0.62, 'recall': 0.64, 'f1_score': 0.63},
                {'threshold': 3.6, 'accuracy': 0.67, 'precision': 0.66, 'recall': 0.68, 'f1_score': 0.67}
            ],
            'correlation_summary': {
                'total_taxa_tested': 20,
                'significant_taxa': 5
            }
        }

    def test_valid_metrics_schema(self):
        """Test that valid metrics pass schema validation."""
        result = validate_model_metrics_schema(self.valid_metrics)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_missing_required_field(self):
        """Test that missing required fields are detected."""
        invalid_metrics = self.valid_metrics.copy()
        del invalid_metrics['mean_accuracy']
        
        result = validate_model_metrics_schema(invalid_metrics)
        self.assertFalse(result['valid'])
        self.assertTrue(any('mean_accuracy' in err for err in result['errors']))

    def test_accuracy_target_logic(self):
        """Test that meets_accuracy_target is correctly set."""
        # Test when accuracy > target
        metrics_high = self.valid_metrics.copy()
        metrics_high['meets_accuracy_target'] = True
        result = validate_model_metrics_schema(metrics_high)
        self.assertTrue(result['valid'])

        # Test when accuracy < target
        metrics_low = self.valid_metrics.copy()
        metrics_low['mean_accuracy'] = 0.50
        metrics_low['meets_accuracy_target'] = False
        result = validate_model_metrics_schema(metrics_low)
        self.assertTrue(result['valid'])

    def test_invalid_pvalue_range(self):
        """Test that p-values outside [0, 1] are detected."""
        invalid_metrics = self.valid_metrics.copy()
        invalid_metrics['significance_pvalue'] = 1.5
        
        result = validate_model_metrics_schema(invalid_metrics)
        self.assertFalse(result['valid'])
        self.assertTrue(any('significance_pvalue' in err for err in result['errors']))

    def test_threshold_details_structure(self):
        """Test that threshold_details is validated correctly."""
        # Valid list of dicts
        valid = self.valid_metrics.copy()
        result = validate_model_metrics_schema(valid)
        self.assertTrue(result['valid'])

        # Invalid: not a list
        invalid = self.valid_metrics.copy()
        invalid['threshold_details'] = "not a list"
        result = validate_model_metrics_schema(invalid)
        self.assertFalse(result['valid'])

        # Invalid: list of non-dicts
        invalid2 = self.valid_metrics.copy()
        invalid2['threshold_details'] = [1, 2, 3]
        result = validate_model_metrics_schema(invalid2)
        self.assertFalse(result['valid'])

    def test_full_integration(self):
        """Test full integration by writing and reading metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_metrics.json')
            
            # Write metrics
            with open(output_path, 'w') as f:
                json.dump(self.valid_metrics, f)
            
            # Read and validate
            with open(output_path, 'r') as f:
                loaded_metrics = json.load(f)
            
            result = validate_model_metrics_schema(loaded_metrics)
            self.assertTrue(result['valid'])

if __name__ == '__main__':
    unittest.main()