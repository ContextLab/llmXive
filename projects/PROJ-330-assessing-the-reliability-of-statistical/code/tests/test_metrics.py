"""
Tests for metrics module.
"""
import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from src.metrics import (
    calculate_pearson_correlation_all_genes,
    calculate_stability_metrics,
    compare_parametric_empirical_pvalues,
    apply_benjamini_hochberg_correction
)

class TestPearsonCorrelationAllGenes:
    def test_pearson_correlation_all_genes_returns_valid_r(self):
        """Test that Pearson correlation returns a valid r value."""
        full = pd.Series([1, 2, 3, 4, 5], index=["g1", "g2", "g3", "g4", "g5"])
        subset = pd.Series([1.1, 2.2, 3.1, 4.2, 5.1], index=["g1", "g2", "g3", "g4", "g5"])
        r = calculate_pearson_correlation_all_genes(full, subset)
        assert -1 <= r <= 1
        assert r > 0.9  # High correlation expected

class TestStabilityMetrics:
    def test_stability_metrics_calculation(self):
        """Test calculation of stability metrics."""
        corrs = [0.9, 0.95, 0.85]
        metrics = calculate_stability_metrics(corrs)
        assert metrics["mean_correlation"] == pytest.approx(0.91, abs=0.01)
        assert metrics["std_correlation"] > 0

class TestCompareParametricEmpiricalPvalues:
    def test_ks_statistic_uniform_distribution_passes(self):
        """Test KS test on uniform distribution."""
        pvals = pd.Series(np.random.uniform(0, 1, 100))
        result = compare_parametric_empirical_pvalues(pvals, pvals)
        assert result["ks_pvalue"] > 0.05  # Should pass uniform test

class TestBlandAltmanPlot:
    def test_bland_altman_plot_generation(self):
        """Test that Bland-Altman plot is generated."""
        from src.metrics import generate_bland_altman_plot
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "plot.png"
            diff = np.random.randn(100)
            mean = np.random.randn(100)
            generate_bland_altman_plot(diff, mean, out_path)
            assert out_path.exists()

class TestBenjaminiHochberg:
    def test_benjamini_hochberg_correction(self):
        """Test BH correction."""
        pvals = pd.Series([0.01, 0.04, 0.03, 0.2])
        corrected = apply_benjamini_hochberg_correction(pvals)
        assert all(corrected.notna())
        assert all(corrected >= 0)
        assert all(corrected <= 1)
