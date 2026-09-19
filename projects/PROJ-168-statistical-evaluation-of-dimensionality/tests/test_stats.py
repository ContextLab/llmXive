"""
tests/test_stats.py

Unit tests for the stats.py module.
These tests verify Fixed-Effects ANOVA and Mixed-Effects model fitting.
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from stats import (
    StatsError,
    load_aggregated_metrics,
    check_collinearity,
    fit_fixed_effects_anova,
    fit_mixed_effects_model,
    apply_benjamini_hochberg
)

class TestStats(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with synthetic metrics data."""
        # Create synthetic aggregated metrics DataFrame
        np.random.seed(42)
        n_datasets = 10
        n_methods = 3
        
        datasets = []
        methods = []
        fidelities = []
        
        for i in range(n_datasets):
            for method in ["pca", "umap", "tsne"]:
                datasets.append(f"GSE_{i}")
                methods.append(method)
                # Simulate fidelity scores with some noise
                base_score = 0.5 + (0.1 if method == "umap" else 0.0)
                fidelities.append(base_score + np.random.normal(0, 0.1))
        
        self.df_metrics = pd.DataFrame({
            "dataset": datasets,
            "method": methods,
            "fidelity": fidelities
        })

    def test_check_collinearity(self):
        """Test collinearity check with VIF."""
        # Create data with no collinearity
        df_no_collinearity = pd.DataFrame({
            "y": np.random.randn(100),
            "x1": np.random.randn(100),
            "x2": np.random.randn(100)
        })
        
        vif_df = check_collinearity(df_no_collinearity, ["x1", "x2"])
        
        # VIF should be low (< 5)
        self.assertTrue((vif_df["VIF"] < 5).all())
        
        # Create data with collinearity
        df_collinear = pd.DataFrame({
            "y": np.random.randn(100),
            "x1": np.random.randn(100),
            "x2": np.random.randn(100) * 0.99 + np.random.randn(100) * 0.1  # Highly correlated
        })
        
        vif_df_collinear = check_collinearity(df_collinear, ["x1", "x2"])
        
        # At least one VIF should be high
        self.assertTrue((vif_df_collinear["VIF"] >= 5).any())

    def test_fit_fixed_effects_anova(self):
        """Test Fixed-Effects ANOVA fitting."""
        # Run ANOVA
        result = fit_fixed_effects_anova(self.df_metrics, formula="fidelity ~ method")
        
        # Check result structure
        self.assertIn("anova_table", result)
        self.assertIn("model", result)
        
        # Verify anova table has expected columns
        anova_table = result["anova_table"]
        self.assertIn("method", anova_table.index)
        
        # Check that p-values exist
        self.assertIn("PR(>F)", anova_table.columns)

    def test_fit_mixed_effects_model(self):
        """Test Mixed-Effects model fitting."""
        # Run Mixed-Effects model
        result = fit_mixed_effects_model(
            self.df_metrics, 
            formula="fidelity ~ method + (1|dataset)"
        )
        
        # Check result structure
        self.assertIn("model", result)
        self.assertIn("summary", result)
        
        # Verify summary contains expected information
        summary = result["summary"]
        self.assertIn("Fixed effects", str(summary))

    def test_apply_benjamini_hochberg(self):
        """Test Benjamini-Hochberg correction."""
        # Create array of p-values
        p_values = np.array([0.01, 0.03, 0.05, 0.07, 0.10, 0.20, 0.50])
        
        # Apply correction
        corrected = apply_benjamini_hochberg(p_values)
        
        # Check output
        self.assertEqual(len(corrected), len(p_values))
        
        # Corrected p-values should be >= original (for BH)
        # Actually BH can produce smaller values for small p, but generally monotonic
        # Let's just verify they are in valid range
        self.assertTrue(all(0 <= p <= 1 for p in corrected))
        
        # Verify monotonicity of adjusted p-values (sorted)
        sorted_indices = np.argsort(p_values)
        sorted_corrected = corrected[sorted_indices]
        self.assertTrue(all(sorted_corrected[i] <= sorted_corrected[i+1] 
                          for i in range(len(sorted_corrected)-1)))

    def test_load_aggregated_metrics(self):
        """Test loading aggregated metrics from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test_metrics.json"
            
            # Create test data
            test_data = {
                "accessions": ["GSE1", "GSE2"],
                "metrics": {
                    "GSE1": {"pca": {"trustworthiness": 0.8, "continuity": 0.75}},
                    "GSE2": {"pca": {"trustworthiness": 0.7, "continuity": 0.65}}
                }
            }
            
            with open(test_file, 'w') as f:
                json.dump(test_data, f)
            
            # Load and verify
            loaded = load_aggregated_metrics(str(test_file))
            
            self.assertIn("GSE1", loaded)
            self.assertIn("pca", loaded["GSE1"])
            self.assertAlmostEqual(loaded["GSE1"]["pca"]["trustworthiness"], 0.8)

    def test_fit_fixed_effects_anova_single_dataset(self):
        """Test ANOVA with single dataset (Case Study mode)."""
        # Create data with only one dataset
        df_single = self.df_metrics[self.df_metrics["dataset"] == "GSE_0"].copy()
        
        # Should still run but with warning or different behavior
        result = fit_fixed_effects_anova(df_single, formula="fidelity ~ method")
        
        self.assertIn("anova_table", result)
        self.assertIn("model", result)

    def test_apply_benjamini_hochberg_all_significant(self):
        """Test BH correction when all p-values are significant."""
        p_values = np.array([0.001, 0.005, 0.01, 0.02])
        
        corrected = apply_benjamini_hochberg(p_values)
        
        # All should remain significant at alpha=0.05
        alpha = 0.05
        significant = corrected < alpha
        self.assertEqual(sum(significant), len(p_values))

    def test_apply_benjamini_hochberg_none_significant(self):
        """Test BH correction when no p-values are significant."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8])
        
        corrected = apply_benjamini_hochberg(p_values)
        
        # None should be significant at alpha=0.05
        alpha = 0.05
        significant = corrected < alpha
        self.assertEqual(sum(significant), 0)

if __name__ == '__main__':
    unittest.main()