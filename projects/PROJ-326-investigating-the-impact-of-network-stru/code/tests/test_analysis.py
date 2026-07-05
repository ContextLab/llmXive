import pytest
import numpy as np
from typing import Dict, Any, List, Tuple
import networkx as nx
from scipy import stats
from statsmodels.stats.multitest import multipletests
from code.src.analysis.sensitivity import run_sensitivity_sweep, validate_sweep_results

class TestLinearRegression:
    def test_simple_linear_regression(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        assert np.isclose(slope, 2.0)
        assert np.isclose(intercept, 0.0)
        assert np.isclose(r_value, 1.0)
        assert p_value < 0.05

    def test_no_correlation(self):
        np.random.seed(42)
        x = np.random.rand(100)
        y = np.random.rand(100)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        assert p_value > 0.05

class TestNonlinearRegression:
    def test_polynomial_fit(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])
        
        coeffs = np.polyfit(x, y, 2)
        p = np.poly1d(coeffs)
        
        assert np.allclose(p(x), y, atol=0.1)
        assert np.isclose(coeffs[0], 1.0, atol=0.1)

class TestEffectSizeCalculation:
    def test_cohen_d(self):
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([2, 3, 4, 5, 6])
        
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
        n1, n2 = len(group1), len(group2)
        
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        cohen_d = (mean2 - mean1) / pooled_std
        
        assert cohen_d < 0

class TestRegressionWithNetworkMetrics:
    def test_clustering_vs_diffusion(self):
        np.random.seed(42)
        clustering_coeffs = np.random.uniform(0.1, 0.9, 50)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, 50)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(clustering_coeffs, diffusion_rates)
        
        assert r_value < 0
        assert p_value < 0.05

class TestANOVATest:
    def test_anova_significant_difference(self):
        group1 = np.random.normal(0, 1, 30)
        group2 = np.random.normal(2, 1, 30)
        group3 = np.random.normal(4, 1, 30)
        
        f_stat, p_value = stats.f_oneway(group1, group2, group3)
        
        assert p_value < 0.05
        assert f_stat > 10

    def test_anova_no_difference(self):
        group1 = np.random.normal(0, 1, 30)
        group2 = np.random.normal(0, 1, 30)
        group3 = np.random.normal(0, 1, 30)
        
        f_stat, p_value = stats.f_oneway(group1, group2, group3)
        
        assert p_value > 0.05

class TestMultipleComparisonCorrection:
    def test_bonferroni_correction(self):
        p_values = np.array([0.01, 0.03, 0.04, 0.06, 0.08])
        
        reject, corrected_p_values, _, _ = multipletests(p_values, alpha=0.05, method='bonferroni')
        
        assert len(reject) == len(p_values)
        assert all(corrected_p_values >= p_values)

    def test_bh_correction(self):
        p_values = np.array([0.01, 0.03, 0.04, 0.06, 0.08])
        
        reject, corrected_p_values, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
        
        assert len(reject) == len(p_values)
        assert all(corrected_p_values >= p_values)

class TestAnalysisIntegration:
    def test_full_analysis_pipeline(self):
        np.random.seed(42)
        n_samples = 100
        
        clustering_coeffs = np.random.uniform(0.1, 0.9, n_samples)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, n_samples)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(clustering_coeffs, diffusion_rates)
        
        assert r_value < 0
        assert p_value < 0.05

class TestSensitivitySweepLogic:
    def test_sweep_generates_required_cutoffs(self):
        np.random.seed(42)
        n_graphs = 100
        clustering_coeffs = np.random.uniform(0.0, 1.0, n_graphs)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, n_graphs)
        
        cutoffs = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        results = run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)
        
        assert len(results) == len(cutoffs)
        for result in results:
            assert 'cutoff' in result
            assert 'n_samples' in result
            assert 'r_value' in result
            assert 'p_value' in result

    def test_sweep_results_match_expectations(self):
        np.random.seed(42)
        n_graphs = 100
        clustering_coeffs = np.random.uniform(0.0, 1.0, n_graphs)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, n_graphs)
        
        cutoffs = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        results = run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)
        
        for result in results:
            assert result['n_samples'] <= n_graphs
            assert -1 <= result['r_value'] <= 1
            assert 0 <= result['p_value'] <= 1

    def test_sweep_with_fewer_cutoffs(self):
        np.random.seed(42)
        n_graphs = 50
        clustering_coeffs = np.random.uniform(0.0, 1.0, n_graphs)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, n_graphs)
        
        cutoffs = [0.2, 0.6]
        
        results = run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)
        
        assert len(results) == len(cutoffs)
        for result in results:
            assert result['n_samples'] <= n_graphs

    def test_sweep_validation_passes(self):
        np.random.seed(42)
        n_graphs = 100
        clustering_coeffs = np.random.uniform(0.0, 1.0, n_graphs)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, n_graphs)
        
        cutoffs = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        results = run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)
        
        is_valid = validate_sweep_results(results, min_cutoffs=5)
        assert is_valid

    def test_sweep_validation_fails_insufficient_cutoffs(self):
        np.random.seed(42)
        n_graphs = 100
        clustering_coeffs = np.random.uniform(0.0, 1.0, n_graphs)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, n_graphs)
        
        cutoffs = [0.1, 0.3]
        
        results = run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)
        
        is_valid = validate_sweep_results(results, min_cutoffs=5)
        assert not is_valid

    def test_sweep_handles_edge_cases(self):
        np.random.seed(42)
        n_graphs = 100
        clustering_coeffs = np.random.uniform(0.0, 1.0, n_graphs)
        diffusion_rates = 0.5 - 0.3 * clustering_coeffs + np.random.normal(0, 0.05, n_graphs)
        
        cutoffs = [0.0, 1.0]
        
        results = run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)
        
        assert len(results) == 2
        for result in results:
            assert result['n_samples'] <= n_graphs
            assert -1 <= result['r_value'] <= 1
            assert 0 <= result['p_value'] <= 1

    def test_sweep_robustness_to_empty_data(self):
        clustering_coeffs = np.array([])
        diffusion_rates = np.array([])
        
        cutoffs = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        with pytest.raises(ValueError):
            run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)

    def test_sweep_robustness_to_mismatched_lengths(self):
        np.random.seed(42)
        clustering_coeffs = np.random.uniform(0.0, 1.0, 100)
        diffusion_rates = np.random.uniform(0.0, 1.0, 50)
        
        cutoffs = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        with pytest.raises(ValueError):
            run_sensitivity_sweep(clustering_coeffs, diffusion_rates, cutoffs)