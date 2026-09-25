"""
Unit tests for bias_null.py
"""
import os
import sys
import unittest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from bias_null import (
    generate_random_background,
    train_bias_null_model,
    predict_bias_null,
    calculate_metrics,
    run_bias_null_model
)

class TestBiasNullModel(unittest.TestCase):
    """Test cases for the bias-only null model."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample presence data
        self.presence_data = pd.DataFrame({
            'decimalLatitude': [40.0, 41.0, 42.0, 40.5, 41.5],
            'decimalLongitude': [-75.0, -76.0, -77.0, -75.5, -76.5],
            'species': ['TestSpecies'] * 5
        })
        
        self.presence_df = self.presence_data.copy()
        self.background_df = generate_random_background(
            self.presence_df, 
            n_samples=100, 
            seed=42
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_generate_random_background(self):
        """Test that random background points are generated within bounds."""
        background = generate_random_background(self.presence_df, n_samples=50, seed=42)
        
        # Check shape
        self.assertEqual(len(background), 50)
        
        # Check columns
        self.assertIn('decimalLatitude', background.columns)
        self.assertIn('decimalLongitude', background.columns)
        
        # Check bounds
        lat_min = self.presence_df['decimalLatitude'].min()
        lat_max = self.presence_df['decimalLatitude'].max()
        lon_min = self.presence_df['decimalLongitude'].min()
        lon_max = self.presence_df['decimalLongitude'].max()
        
        self.assertTrue((background['decimalLatitude'] >= lat_min).all())
        self.assertTrue((background['decimalLatitude'] <= lat_max).all())
        self.assertTrue((background['decimalLongitude'] >= lon_min).all())
        self.assertTrue((background['decimalLongitude'] <= lon_max).all())

    def test_train_bias_null_model(self):
        """Test that the null model calculates correct prevalence."""
        model_params = train_bias_null_model(self.presence_df, self.background_df, seed=42)
        
        # Check that prevalence is calculated correctly
        expected_prevalence = len(self.presence_df) / (len(self.presence_df) + len(self.background_df))
        self.assertAlmostEqual(model_params['prevalence'], expected_prevalence, places=6)
        
        # Check that counts are correct
        self.assertEqual(model_params['n_presence'], len(self.presence_df))
        self.assertEqual(model_params['n_background'], len(self.background_df))

    def test_predict_bias_null(self):
        """Test that predictions are constant (prevalence)."""
        model_params = train_bias_null_model(self.presence_df, self.background_df, seed=42)
        predictions = predict_bias_null(model_params, n_samples=100)
        
        # All predictions should be equal to prevalence
        expected_pred = model_params['prevalence']
        self.assertTrue(np.allclose(predictions, expected_pred))

    def test_calculate_metrics(self):
        """Test AUC and TSS calculation."""
        # Create synthetic labels
        y_true = np.array([1] * 50 + [0] * 50)
        y_pred_proba = np.array([0.5] * 100)  # Null model predicts constant 0.5
        
        metrics = calculate_metrics(y_true, y_pred_proba)
        
        # AUC should be 0.5 for random predictions
        self.assertAlmostEqual(metrics['auc'], 0.5, places=1)
        
        # TSS should be 0 for random predictions (sensitivity + specificity - 1 = 0.5 + 0.5 - 1 = 0)
        self.assertAlmostEqual(metrics['tss'], 0.0, places=1)

    def test_run_bias_null_model(self):
        """Test the full pipeline for a single species."""
        # Create temporary CSV file
        temp_csv = os.path.join(self.temp_dir, 'test_occurrence.csv')
        self.presence_data.to_csv(temp_csv, index=False)
        
        result = run_bias_null_model(
            species_name='TestSpecies',
            data_path=temp_csv,
            n_background=50,
            seed=42
        )
        
        # Check result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['species'], 'TestSpecies')
        self.assertEqual(result['algorithm'], 'bias_null_random')
        self.assertIn('auc', result)
        self.assertIn('tss', result)
        
        # Check that AUC and TSS are in valid ranges
        self.assertGreaterEqual(result['auc'], 0.0)
        self.assertLessEqual(result['auc'], 1.0)
        self.assertGreaterEqual(result['tss'], -1.0)
        self.assertLessEqual(result['tss'], 1.0)

    def test_run_bias_null_model_insufficient_data(self):
        """Test handling of species with insufficient data."""
        # Create DataFrame with very few records
        small_data = pd.DataFrame({
            'decimalLatitude': [40.0],
            'decimalLongitude': [-75.0],
            'species': ['SmallSpecies']
        })
        
        temp_csv = os.path.join(self.temp_dir, 'small_occurrence.csv')
        small_data.to_csv(temp_csv, index=False)
        
        result = run_bias_null_model(
            species_name='SmallSpecies',
            data_path=temp_csv,
            n_background=10,
            seed=42
        )
        
        # Should return None for insufficient data
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
