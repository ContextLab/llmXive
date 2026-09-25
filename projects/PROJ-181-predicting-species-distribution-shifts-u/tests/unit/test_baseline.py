"""
Unit tests for the baseline model implementation.
"""

import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import unittest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.baseline import (
    calculate_prevalence,
    predict_baseline,
    calculate_baseline_metrics,
    save_baseline_metrics
)

class TestBaselineModel(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_records = [
            {'species': 'test_species', 'presence': 1, 'latitude': 45.0, 'longitude': -75.0},
            {'species': 'test_species', 'presence': 1, 'latitude': 46.0, 'longitude': -76.0},
            {'species': 'test_species', 'presence': 1, 'latitude': 47.0, 'longitude': -77.0},
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        pass
    
    def test_calculate_prevalence_all_present(self):
        """Test prevalence calculation with all presences."""
        prevalence = calculate_prevalence(self.test_records)
        self.assertEqual(prevalence, 1.0)
    
    def test_calculate_prevalence_empty(self):
        """Test prevalence calculation with empty list."""
        prevalence = calculate_prevalence([])
        self.assertEqual(prevalence, 0.0)
    
    def test_predict_baseline(self):
        """Test baseline prediction generation."""
        prevalence = 0.3
        predictions = predict_baseline(self.test_records, prevalence)
        
        self.assertEqual(len(predictions), 3)
        for pred in predictions:
            self.assertEqual(pred['species'], 'test_species')
            self.assertEqual(pred['predicted_probability'], prevalence)
            self.assertEqual(pred['actual_presence'], 1)
    
    def test_calculate_baseline_metrics(self):
        """Test baseline metrics calculation."""
        prevalence = 0.5
        predictions = predict_baseline(self.test_records, prevalence)
        metrics = calculate_baseline_metrics(predictions)
        
        self.assertEqual(metrics['algorithm'], 'null_prevalence')
        self.assertEqual(metrics['auc'], 0.5)
        self.assertEqual(metrics['tss'], 0.0)
        self.assertEqual(metrics['threshold'], prevalence)
    
    def test_calculate_baseline_metrics_empty(self):
        """Test baseline metrics calculation with empty predictions."""
        metrics = calculate_baseline_metrics([])
        
        self.assertEqual(metrics['algorithm'], 'null_prevalence')
        self.assertEqual(metrics['auc'], 0.5)
        self.assertEqual(metrics['tss'], 0.0)
        self.assertEqual(metrics['threshold'], 0.5)
    
    def test_save_baseline_metrics(self):
        """Test saving baseline metrics to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_baseline.csv"
            
            metrics = {
                'species': 'test_species',
                'algorithm': 'null_prevalence',
                'auc': 0.5,
                'tss': 0.0,
                'threshold': 0.5
            }
            
            save_baseline_metrics(metrics, output_path)
            
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['species'], 'test_species')
            self.assertEqual(rows[0]['algorithm'], 'null_prevalence')
            self.assertEqual(float(rows[0]['auc']), 0.5)
            self.assertEqual(float(rows[0]['tss']), 0.0)
            self.assertEqual(float(rows[0]['threshold']), 0.5)
    
    def test_save_baseline_metrics_append(self):
        """Test appending multiple metrics to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_baseline.csv"
            
            # Write first record
            metrics1 = {
                'species': 'species1',
                'algorithm': 'null_prevalence',
                'auc': 0.5,
                'tss': 0.0,
                'threshold': 0.5
            }
            save_baseline_metrics(metrics1, output_path)
            
            # Write second record
            metrics2 = {
                'species': 'species2',
                'algorithm': 'null_prevalence',
                'auc': 0.5,
                'tss': 0.0,
                'threshold': 0.6
            }
            save_baseline_metrics(metrics2, output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['species'], 'species1')
            self.assertEqual(rows[1]['species'], 'species2')
            self.assertEqual(float(rows[1]['threshold']), 0.6)

if __name__ == '__main__':
    unittest.main()