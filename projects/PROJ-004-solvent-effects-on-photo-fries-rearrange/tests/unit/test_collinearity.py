import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path for imports if running from tests/
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.correlation import calculate_vif, perform_vif_analysis

class TestVIFCalculation:
    """Unit tests for Variance Inflation Factor (VIF) calculation logic."""

    def test_vif_perfect_collinearity_raises_error(self):
        """VIF should raise an error if perfect collinearity exists (determinant is 0)."""
        # Create a dataframe with perfect collinearity (x2 = 2 * x1)
        data = pd.DataFrame({
            'intercept': [1.0] * 10,
            'x1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'x2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Perfectly collinear with x1
        })
        
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            calculate_vif(data)

    def test_vif_independence_returns_one(self):
        """VIF should be close to 1.0 for independent variables."""
        # Generate independent random data
        np.random.seed(42)
        data = pd.DataFrame({
            'intercept': [1.0] * 50,
            'x1': np.random.randn(50),
            'x2': np.random.randn(50),
            'x3': np.random.randn(50)
        })
        
        vif_results = calculate_vif(data)
        
        # VIF for independent variables should be approximately 1
        for var in ['x1', 'x2', 'x3']:
            assert 1.0 <= vif_results[var] < 1.1, f"VIF for {var} should be ~1.0, got {vif_results[var]}"

    def test_vif_high_collinearity_returns_high_value(self):
        """VIF should be significantly > 1 for highly correlated variables."""
        np.random.seed(42)
        n = 50
        base = np.random.randn(n)
        data = pd.DataFrame({
            'intercept': [1.0] * n,
            'x1': base,
            'x2': base + 0.05 * np.random.randn(n)  # Highly correlated with x1
        })
        
        vif_results = calculate_vif(data)
        
        # VIF should be high (typically > 5 or 10 indicates problematic collinearity)
        assert vif_results['x1'] > 5.0, f"VIF for x1 should be > 5.0, got {vif_results['x1']}"
        assert vif_results['x2'] > 5.0, f"VIF for x2 should be > 5.0, got {vif_results['x2']}"

    def test_vif_single_predictor_returns_one(self):
        """VIF should be 1.0 when only one predictor exists."""
        data = pd.DataFrame({
            'intercept': [1.0] * 10,
            'x1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        
        vif_results = calculate_vif(data)
        assert vif_results['x1'] == 1.0

    def test_perform_vif_analysis_integration(self):
        """Test the full VIF analysis pipeline with realistic solvent data."""
        # Simulate a small dataset similar to what T029/T030 would produce
        # Solvents with varying dielectric constants and solvation energies
        np.random.seed(123)
        n_solvents = 6
        
        # Create correlated predictors to simulate real-world solvent properties
        dielectric_base = np.random.uniform(2.0, 10.0, n_solvents)
        # Solvation energy is correlated with dielectric but not perfectly
        solvation_energy = dielectric_base * -2.5 + np.random.normal(0, 0.5, n_solvents)
        # A third variable slightly correlated
        refractive_index = 1.3 + (dielectric_base * 0.02) + np.random.normal(0, 0.01, n_solvents)
        
        df = pd.DataFrame({
            'intercept': 1.0,
            'dielectric_constant': dielectric_base,
            'solvation_energy': solvation_energy,
            'refractive_index': refractive_index
        })
        
        vif_results = perform_vif_analysis(df, target_col='solvation_energy')
        
        # Verify structure of results
        assert isinstance(vif_results, dict)
        assert 'dielectric_constant' in vif_results
        assert 'refractive_index' in vif_results
        
        # Values should be positive
        assert all(v > 0 for v in vif_results.values())

    def test_vif_threshold_flagging(self):
        """Test that high VIF values are correctly identified."""
        np.random.seed(42)
        n = 30
        base = np.random.randn(n)
        data = pd.DataFrame({
            'intercept': [1.0] * n,
            'x1': base,
            'x2': base + 0.1 * np.random.randn(n)
        })
        
        vif_results = calculate_vif(data)
        
        # With high correlation, VIF should exceed common thresholds (e.g., 5 or 10)
        # We just verify the calculation runs and returns high values
        assert max(vif_results.values()) > 5.0, "Expected high VIF for correlated variables"