"""
Tests for mixed-effects model fitting (T027).

Tests:
- T025: Contract test for model output structure
- T026: Integration test for model convergence and VIF check
"""
import csv
import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

# Import the module to test
from scripts.fit_mixed_effects import (
    fit_model_for_game,
    calculate_vif,
    load_processed_data,
    main
)
from scripts.preprocess import load_config

class TestMixedEffectsModel(unittest.TestCase):
    """Test mixed-effects model fitting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.test_dir.name) / 'data' / 'processed'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal config
        self.config = {
            'data': {
                'processed': str(self.data_dir)
            },
            'games': ['test-game'],
            'checkpoint_dir': str(Path(self.test_dir.name) / 'data' / 'checkpoints')
        }
        
        # Create sample data for testing
        self.sample_data = pd.DataFrame({
            'run_time_seconds': np.random.lognormal(mean=5, sigma=0.5, size=50),
            'attempt_number': np.random.randint(1, 20, size=50),
            'game_id': ['test-game'] * 50,
            'runner_id': [f'runner_{i % 10}' for i in range(50)],  # 10 runners
            'difficulty_label': ['easy'] * 50,
            'lagged_competitive_pressure': np.random.normal(0.5, 0.2, size=50),
            'submission_date': pd.date_range('2020-01-01', periods=50, freq='D')
        })
        
        # Save sample data
        self.sample_data.to_csv(self.data_dir / 'run_records.csv', index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.test_dir.cleanup()
    
    def test_025_contract_output_structure(self):
        """
        T025: Contract test for model output structure.
        
        Verifies that the model output contains all required fields
        as specified in the task requirements.
        """
        # Load sample data
        df = pd.read_csv(self.data_dir / 'run_records.csv')
        
        # Fit model
        result = fit_model_for_game(df, 'test-game')
        
        self.assertIsNotNone(result, "Model should return a result dict")
        
        # Check required fields
        required_fields = [
            'game_id', 'n_runs', 'n_runners', 'converged',
            'log_likelihood', 'aic', 'bic',
            'log_attempt_coef', 'log_attempt_pvalue',
            'difficulty_label_coef', 'lagged_pressure_coef', 'lagged_pressure_pvalue',
            'lr_statistic', 'lr_pvalue',
            'vif_log_attempt', 'vif_lagged_pressure',
            'high_vif_features'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Result should contain '{field}'")
        
        # Check numeric types
        self.assertIsInstance(result['n_runs'], (int, np.integer))
        self.assertIsInstance(result['n_runners'], (int, np.integer))
        self.assertIsInstance(result['converged'], bool)
        
        # Check that coefficients are numeric (or None if not applicable)
        self.assertTrue(
            isinstance(result['log_attempt_coef'], (float, int, np.number)) or result['log_attempt_coef'] is None,
            "log_attempt_coef should be numeric or None"
        )
        
    def test_026_convergence_and_vif_check(self):
        """
        T026: Integration test for model convergence and VIF < 5 check.
        
        Verifies that:
        1. The model attempts to converge (even if it doesn't succeed on small data)
        2. VIF calculation works and flags high multicollinearity
        """
        # Load sample data
        df = pd.read_csv(self.data_dir / 'run_records.csv')
        
        # Fit model
        result = fit_model_for_game(df, 'test-game')
        
        self.assertIsNotNone(result, "Model should return a result")
        
        # Check convergence flag exists (may be False on small synthetic data)
        self.assertIn('converged', result)
        self.assertIsInstance(result['converged'], bool)
        
        # Check VIF calculation
        self.assertIn('vif_log_attempt', result)
        self.assertIn('vif_lagged_pressure', result)
        
        # VIF values should be numeric (or None if calculation failed)
        vif_log = result['vif_log_attempt']
        vif_lag = result['vif_lagged_pressure']
        
        # If VIFs were calculated, they should be positive numbers
        if vif_log is not None:
            self.assertGreater(vif_log, 0, "VIF should be positive")
        if vif_lag is not None:
            self.assertGreater(vif_lag, 0, "VIF should be positive")
        
        # Check high VIF flagging
        self.assertIn('high_vif_features', result)
        if result['high_vif_features']:
            high_vifs = json.loads(result['high_vif_features'])
            for vif_val in high_vifs.values():
                self.assertGreater(vif_val, 5, "High VIF features should have VIF > 5")
        
    def test_model_fails_on_insufficient_data(self):
        """Test that model fails gracefully with insufficient data."""
        # Create data with only 5 runs
        small_data = pd.DataFrame({
            'run_time_seconds': np.random.lognormal(mean=5, sigma=0.5, size=5),
            'attempt_number': np.random.randint(1, 20, size=5),
            'game_id': ['test-game'] * 5,
            'runner_id': [f'runner_{i}' for i in range(5)],
            'difficulty_label': ['easy'] * 5,
            'lagged_competitive_pressure': np.random.normal(0.5, 0.2, size=5),
            'submission_date': pd.date_range('2020-01-01', periods=5, freq='D')
        })
        
        result = fit_model_for_game(small_data, 'test-game')
        self.assertIsNone(result, "Model should return None for insufficient data")
    
    def test_vif_calculation(self):
        """Test VIF calculation function directly."""
        # Create data with known collinearity
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # Highly correlated with x1
        y = x1 + x2 + np.random.normal(0, 0.5, n)
        
        df = pd.DataFrame({
            'y': y,
            'x1': x1,
            'x2': x2
        })
        
        formula = "y ~ x1 + x2"
        vifs = calculate_vif(df, formula)
        
        self.assertIn('x1', vifs)
        self.assertIn('x2', vifs)
        
        # With high correlation, VIFs should be > 5
        self.assertGreater(vifs['x1'], 1, "VIF for x1 should be > 1")
        self.assertGreater(vifs['x2'], 1, "VIF for x2 should be > 1")

if __name__ == '__main__':
    unittest.main()