import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from src.metrics import (
    calculate_pvalue_inflation,
    calculate_pearson_correlation_all_genes,
    calculate_stability_metrics,
    compare_parametric_empirical_pvalues,
    apply_benjamini_hochberg_correction,
    generate_bland_altman_plot
)

class TestPValueInflation:
    """Tests for calculate_pvalue_inflation function (T024)."""

    def test_calculate_pvalue_inflation_basic(self):
        """Test basic MAD calculation with simple data."""
        # Create synthetic but realistic p-values
        np.random.seed(42)
        n_genes = 1000
        parametric = pd.Series(np.random.beta(0.5, 5, n_genes), index=[f"gene_{i}" for i in range(n_genes)])
        # Empirical is slightly shifted (simulating inflation)
        empirical = pd.Series(np.random.beta(0.5, 5, n_genes) * 1.1, index=parametric.index)
        
        result = calculate_pvalue_inflation(parametric, empirical)
        
        assert "mad" in result
        assert "median_difference" in result
        assert "mean_difference" in result
        assert "inflation_ratio" in result
        assert isinstance(result["mad"], float)
        assert result["mad"] >= 0

    def test_calculate_pvalue_inflation_perfect_match(self):
        """Test MAD is near zero when p-values match perfectly."""
        pvals = pd.Series([0.01, 0.05, 0.1, 0.5, 0.9], index=["g1", "g2", "g3", "g4", "g5"])
        
        result = calculate_pvalue_inflation(pvals, pvals)
        
        assert result["mad"] < 1e-10
        assert result["median_difference"] == 0.0
        assert result["inflation_ratio"] == 1.0

    def test_calculate_pvalue_inflation_no_overlap(self):
        """Test error when no overlapping genes."""
        p1 = pd.Series([0.1, 0.2], index=["a", "b"])
        p2 = pd.Series([0.3, 0.4], index=["c", "d"])
        
        with pytest.raises(ValueError, match="No overlapping genes"):
            calculate_pvalue_inflation(p1, p2)

    def test_calculate_pvalue_inflation_with_nan(self):
        """Test handling of NaN values (should be filtered)."""
        p1 = pd.Series([0.1, np.nan, 0.3], index=["a", "b", "c"])
        p2 = pd.Series([0.15, 0.25, 0.35], index=["a", "b", "c"])
        
        result = calculate_pvalue_inflation(p1, p2)
        
        # Should only use 'a' and 'c'
        assert result["mad"] >= 0

class TestPearsonCorrelationAllGenes:
    """Tests for calculate_pearson_correlation_all_genes (T016/T024 context)."""

    def test_pearson_correlation_all_genes_basic(self):
        """Test basic correlation calculation."""
        genes = [f"gene_{i}" for i in range(100)]
        full = pd.Series(np.random.randn(100), index=genes)
        subset = pd.Series(np.random.randn(100) * 0.8 + full.values * 0.2, index=genes)
        
        r = calculate_pearson_correlation_all_genes(full, subset)
        
        assert -1.0 <= r <= 1.0

    def test_pearson_correlation_all_genes_no_overlap(self):
        """Test error when no overlap."""
        full = pd.Series([1, 2], index=["a", "b"])
        subset = pd.Series([3, 4], index=["c", "d"])
        
        with pytest.raises(ValueError, match="No overlapping genes"):
            calculate_pearson_correlation_all_genes(full, subset)

    def test_pearson_correlation_all_genes_insufficient_data(self):
        """Test error with too few overlapping genes."""
        full = pd.Series([1, 2], index=["a", "b"])
        subset = pd.Series([3, 2], index=["a", "b"])
        
        with pytest.raises(ValueError, match="Insufficient overlapping genes"):
            calculate_pearson_correlation_all_genes(full, subset)

class TestStabilityMetrics:
    """Tests for calculate_stability_metrics."""

    def test_calculate_stability_metrics(self):
        """Test stability metrics calculation."""
        correlations = [0.8, 0.85, 0.75, 0.9, 0.82]
        result = calculate_stability_metrics(correlations)
        
        assert result["mean_correlation"] == pytest.approx(0.824, rel=0.01)
        assert result["std_correlation"] > 0
        assert result["min_correlation"] == 0.75
        assert result["max_correlation"] == 0.9

    def test_calculate_stability_metrics_empty(self):
        """Test with empty list."""
        result = calculate_stability_metrics([])
        assert result["mean_correlation"] == 0.0

class TestCompareParametricEmpiricalPvalues:
    """Tests for compare_parametric_empirical_pvalues (T024b context)."""

    def test_compare_parametric_empirical_pvalues_ks(self):
        """Test KS test and Bland-Altman metrics."""
        np.random.seed(42)
        n = 500
        p_param = pd.Series(np.random.beta(0.5, 5, n), index=[f"gene_{i}" for i in range(n)])
        p_emp = pd.Series(np.random.beta(0.5, 5, n), index=p_param.index)
        
        result = compare_parametric_empirical_pvalues(p_param, p_emp)
        
        assert "ks_statistic" in result
        assert "ks_pvalue" in result
        assert "uniformity_pass" in result
        assert isinstance(result["ks_statistic"], float)
        assert 0 <= result["ks_pvalue"] <= 1

    def test_compare_parametric_empirical_pvalues_non_uniform(self):
        """Test with non-uniform empirical p-values (e.g., conservative)."""
        # Create conservative p-values (shifted towards 1)
        np.random.seed(42)
        n = 500
        p_param = pd.Series(np.random.beta(0.5, 5, n), index=[f"gene_{i}" for i in range(n)])
        p_emp = pd.Series(np.random.beta(2, 1, n), index=p_param.index) # Shifted towards 1
        
        result = compare_parametric_empirical_pvalues(p_param, p_emp)
        
        assert "mean_difference" in result
        assert "std_difference" in result
        assert "correlation" in result

class TestBenjaminiHochberg:
    """Tests for apply_benjamini_hochberg_correction."""

    def test_apply_benjamini_hochberg_correction(self):
        """Test BH correction on simple data."""
        pvals = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05], index=["a", "b", "c", "d", "e"])
        corrected = apply_benjamini_hochberg_correction(pvals)
        
        assert len(corrected) == 5
        assert all(0 <= x <= 1 for x in corrected.dropna())
        # Corrected values should generally be larger than raw
        assert all(corrected >= pvals)

    def test_apply_benjamini_hochberg_correction_with_nan(self):
        """Test BH correction with NaN values."""
        pvals = pd.Series([0.01, np.nan, 0.03], index=["a", "b", "c"])
        corrected = apply_benjamini_hochberg_correction(pvals)
        
        assert pd.isna(corrected["b"])
        assert not pd.isna(corrected["a"])
        assert not pd.isna(corrected["c"])

class TestBlandAltmanPlot:
    """Tests for generate_bland_altman_plot."""

    def test_generate_bland_altman_plot(self):
        """Test plot generation."""
        np.random.seed(42)
        n = 100
        p_param = pd.Series(np.random.beta(0.5, 5, n), index=[f"gene_{i}" for i in range(n)])
        p_emp = pd.Series(np.random.beta(0.5, 5, n), index=p_param.index)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bland_altman.png"
            result_path = generate_bland_altman_plot(p_param, p_emp, output_path)
            
            assert result_path.exists()
            assert result_path.suffix == ".png"
            assert result_path.stat().st_size > 1000  # File should have content

    def test_generate_bland_altman_plot_no_data(self):
        """Test error with no valid data."""
        p1 = pd.Series([np.nan], index=["a"])
        p2 = pd.Series([np.nan], index=["a"])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bland_altman.png"
            with pytest.raises(ValueError, match="No valid data points"):
                generate_bland_altman_plot(p1, p2, output_path)