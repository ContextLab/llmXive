"""
Unit tests for the Power Analysis module (T019).
"""

import math
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

import numpy as np
import pandas as pd

# Import the module under test
try:
    from power_analysis import (
        calculate_theoretical_power,
        calculate_required_n,
        generate_synthetic_dataset,
        run_power_analysis,
        calculate_theoretical_power,
        TRUE_BETA,
        TARGET_POWER,
        SIGNIFICANCE_LEVEL
    )
except ImportError:
    # If running in isolation without full project setup, mock dependencies
    raise unittest.SkipTest("Could not import power_analysis module. Ensure project structure is correct.")

class TestPowerAnalysisCalculations(unittest.TestCase):

    def test_calculate_theoretical_power_small_n(self):
        """Test power calculation with small sample size."""
        n = 20
        beta = 0.5
        power = calculate_theoretical_power(n, beta)
        self.assertGreater(power, 0.0)
        self.assertLess(power, 1.0)

    def test_calculate_theoretical_power_large_n(self):
        """Test power calculation with large sample size approaches 1."""
        n = 1000
        beta = 0.1
        power = calculate_theoretical_power(n, beta)
        self.assertGreater(power, 0.9)

    def test_calculate_required_n(self):
        """Test that required N is calculated correctly."""
        # With a larger effect size, N should be smaller
        n_small_effect = calculate_required_n(0.1, 0.80)
        n_large_effect = calculate_required_n(0.5, 0.80)
        
        self.assertGreater(n_small_effect, n_large_effect)
        self.assertGreater(n_small_effect, 0)

    def test_generate_synthetic_dataset_structure(self):
        """Test that the generated dataset has the correct columns."""
        n = 100
        df = generate_synthetic_dataset(n, beta=0.1)
        
        expected_columns = ['participant_id', 'microbiome_ilr', 'cognitive_score', 'age', 'sex', 'bmi']
        self.assertListEqual(list(df.columns), expected_columns)
        self.assertEqual(len(df), n)

    def test_generate_synthetic_dataset_beta(self):
        """Test that the generated dataset reflects the input beta approximately."""
        np.random.seed(42)
        n = 10000
        beta = 0.5
        df = generate_synthetic_dataset(n, beta=beta)
        
        # Regression to estimate beta
        from scipy import stats
        slope, intercept, r_value, p_value, std_err = stats.linregress(df['microbiome_ilr'], df['cognitive_score'])
        
        # Allow some tolerance due to noise
        self.assertAlmostEqual(slope, beta, delta=0.1)

    def test_run_power_analysis_returns_dict(self):
        """Test that run_power_analysis returns a dictionary with expected keys."""
        np.random.seed(42)
        n = 100
        df = generate_synthetic_dataset(n, beta=0.1)
        
        results = run_power_analysis(df)
        
        expected_keys = ['n', 'beta_hat', 'true_beta', 'p_value', 't_statistic', 'se', 'r_squared', 'theoretical_power', 'observed_power']
        for key in expected_keys:
            self.assertIn(key, results)

    def test_power_gate_validation_logic(self):
        """Test the logic used for the power gate."""
        # If N is very small, power should be low
        n = 10
        power = calculate_theoretical_power(n, 0.1)
        self.assertLess(power, 0.5) # Likely low power

class TestPowerAnalysisIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self):
        """Test the full pipeline from generation to analysis."""
        np.random.seed(42)
        n = 500
        beta = 0.1
        
        df = generate_synthetic_dataset(n, beta)
        results = run_power_analysis(df, beta)
        
        # Check that beta_hat is close to beta
        self.assertAlmostEqual(results['beta_hat'], beta, delta=0.05)
        
        # Check that theoretical power is calculated
        self.assertGreater(results['theoretical_power'], 0.0)

if __name__ == '__main__':
    unittest.main()