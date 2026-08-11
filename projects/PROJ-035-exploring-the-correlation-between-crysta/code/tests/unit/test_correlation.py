"""
Unit tests for correlation analysis module.

Tests Pearson and Spearman correlation calculations,
Benjamini-Hochberg correction, and stratified analysis.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.correlation import (
    calculate_pearson_correlation,
    calculate_spearman_correlation,
    benjamini_hochberg_correction,
    compute_correlation_matrix,
    stratified_correlation_analysis,
    DESCRIPTOR_COLUMNS,
    TARGET_COLUMN,
    MIN_SAMPLES_FOR_CORRELATION
)


class TestPearsonCorrelation:
    """Tests for Pearson correlation calculation."""

    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        corr, p_val = calculate_pearson_correlation(x, y)
        assert np.isclose(corr, 1.0, atol=1e-6)
        assert p_val < 0.05

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        corr, p_val = calculate_pearson_correlation(x, y)
        assert np.isclose(corr, -1.0, atol=1e-6)
        assert p_val < 0.05

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        corr, p_val = calculate_pearson_correlation(x, y)
        assert abs(corr) < 0.3  # Should be weak correlation

    def test_insufficient_samples(self):
        """Test with too few samples."""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        corr, p_val = calculate_pearson_correlation(x, y)
        assert np.isnan(corr)
        assert np.isnan(p_val)

    def test_zero_variance(self):
        """Test with zero variance in one variable."""
        x = np.array([1, 1, 1, 1, 1])
        y = np.array([1, 2, 3, 4, 5])
        corr, p_val = calculate_pearson_correlation(x, y)
        assert np.isnan(corr)
        assert np.isnan(p_val)


class TestSpearmanCorrelation:
    """Tests for Spearman correlation calculation."""

    def test_perfect_rank_correlation(self):
        """Test with perfectly rank-correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        corr, p_val = calculate_spearman_correlation(x, y)
        assert np.isclose(corr, 1.0, atol=1e-6)
        assert p_val < 0.05

    def test_nonlinear_monotonic(self):
        """Test with nonlinear but monotonic relationship."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])  # Quadratic
        corr, p_val = calculate_spearman_correlation(x, y)
        assert np.isclose(corr, 1.0, atol=1e-6)
        assert p_val < 0.05

    def test_insufficient_samples(self):
        """Test with too few samples."""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        corr, p_val = calculate_spearman_correlation(x, y)
        assert np.isnan(corr)
        assert np.isnan(p_val)


class TestBenjaminiHochbergCorrection:
    """Tests for BH correction."""

    def test_basic_correction(self):
        """Test basic BH correction."""
        p_values = np.array([0.01, 0.03, 0.04, 0.06, 0.10])
        adjusted = benjamini_hochberg_correction(p_values)
        assert len(adjusted) == len(p_values)
        # Adjusted values should be >= original
        assert all(adjusted >= p_values - 1e-10)

    def test_all_significant(self):
        """Test with all small p-values."""
        p_values = np.array([0.001, 0.002, 0.003])
        adjusted = benjamini_hochberg_correction(p_values)
        assert all(adjusted < 0.05)

    def test_all_insignificant(self):
        """Test with all large p-values."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8])
        adjusted = benjamini_hochberg_correction(p_values)
        assert all(adjusted >= 0.05)

    def test_empty_array(self):
        """Test with empty array."""
        p_values = np.array([])
        adjusted = benjamini_hochberg_correction(p_values)
        assert len(adjusted) == 0


class TestCorrelationMatrix:
    """Tests for correlation matrix computation."""

    def create_test_dataframe(self, n_samples=50):
        """Create a test dataframe with descriptors and target."""
        np.random.seed(42)
        df = pd.DataFrame({
            'tolerance_factor': np.random.randn(n_samples) * 0.1 + 1.0,
            'octahedral_tilting_angle': np.random.randn(n_samples) * 5.0,
            'bond_length_variance': np.random.randn(n_samples) * 0.01 + 0.05,
            'unit_cell_volume': np.random.randn(n_samples) * 10.0 + 100.0,
            'thermal_conductivity_normalized': np.random.randn(n_samples) * 0.5 + 1.0,
            'chemistry_class': np.random.choice(['oxide', 'halide', 'nitride'], n_samples)
        })
        # Add some correlation
        df['thermal_conductivity_normalized'] += 0.3 * df['tolerance_factor']
        return df

    def test_compute_pearson_matrix(self):
        """Test Pearson correlation matrix computation."""
        df = self.create_test_dataframe()
        results = compute_correlation_matrix(
            df,
            descriptors=DESCRIPTOR_COLUMNS,
            target=TARGET_COLUMN,
            method='pearson'
        )

        assert 'correlations' in results
        assert 'p_values' in results
        assert 'adjusted_p_values' in results
        assert 'significance' in results

        # Check that all descriptors are present
        for desc in DESCRIPTOR_COLUMNS:
            assert desc in results['correlations']
            assert desc in results['p_values']

    def test_compute_spearman_matrix(self):
        """Test Spearman correlation matrix computation."""
        df = self.create_test_dataframe()
        results = compute_correlation_matrix(
            df,
            descriptors=DESCRIPTOR_COLUMNS,
            target=TARGET_COLUMN,
            method='spearman'
        )

        assert len(results['correlations']) == len(DESCRIPTOR_COLUMNS)

    def test_missing_columns(self):
        """Test with missing columns."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        results = compute_correlation_matrix(
            df,
            descriptors=['a', 'missing'],
            target='b'
        )
        # Should handle missing column gracefully
        assert 'a' in results['correlations']
        assert 'missing' not in results['correlations']


class TestStratifiedAnalysis:
    """Tests for stratified correlation analysis."""

    def test_stratified_by_chemistry(self):
        """Test stratified analysis by chemistry class."""
        np.random.seed(42)
        n_samples = 150
        df = pd.DataFrame({
            'tolerance_factor': np.random.randn(n_samples) * 0.1 + 1.0,
            'octahedral_tilting_angle': np.random.randn(n_samples) * 5.0,
            'bond_length_variance': np.random.randn(n_samples) * 0.01 + 0.05,
            'unit_cell_volume': np.random.randn(n_samples) * 10.0 + 100.0,
            'thermal_conductivity_normalized': np.random.randn(n_samples) * 0.5 + 1.0,
            'chemistry_class': np.random.choice(['oxide', 'halide', 'nitride'], n_samples)
        })

        results = stratified_correlation_analysis(
            df,
            descriptors=DESCRIPTOR_COLUMNS,
            target=TARGET_COLUMN,
            stratification_column='chemistry_class'
        )

        assert 'oxide' in results
        assert 'halide' in results
        assert 'nitride' in results

        # Check that each stratum has required keys
        for stratum, stratum_results in results.items():
            assert 'correlations' in stratum_results
            assert 'n_samples' in stratum_results

    def test_insufficient_samples_stratum(self):
        """Test with stratum having insufficient samples."""
        np.random.seed(42)
        df = pd.DataFrame({
            'tolerance_factor': np.random.randn(50) * 0.1 + 1.0,
            'octahedral_tilting_angle': np.random.randn(50) * 5.0,
            'bond_length_variance': np.random.randn(50) * 0.01 + 0.05,
            'unit_cell_volume': np.random.randn(50) * 10.0 + 100.0,
            'thermal_conductivity_normalized': np.random.randn(50) * 0.5 + 1.0,
            'chemistry_class': ['oxide'] * 45 + ['halide'] * 5  # halide has too few
        })

        results = stratified_correlation_analysis(
            df,
            descriptors=DESCRIPTOR_COLUMNS,
            target=TARGET_COLUMN,
            stratification_column='chemistry_class'
        )

        # halide should have 0 correlations due to insufficient samples
        assert results['halide']['n_samples'] == 5
        assert len(results['halide']['correlations']) == 0

    def test_missing_stratification_column(self):
        """Test with missing stratification column."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        with pytest.raises(ValueError):
            stratified_correlation_analysis(
                df,
                descriptors=['a'],
                target='a',
                stratification_column='missing'
            )