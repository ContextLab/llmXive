import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

# Import the functions we are testing
# Note: These functions are expected to be in src/analysis/statistics.py
# which is not yet implemented, so we will test the logic assuming they exist
# or we will mock them if they don't. However, per the task description,
# we are writing the tests for Hartigan's dip test and GMM bimodality assessment.
# Since the implementation (T034) is not done, we will structure the tests
# to verify the *logic* of the assessment when the implementation is ready.
# We will import from src.analysis.statistics if available, otherwise mock.

try:
    from src.analysis.statistics import assess_bimodality_and_fallback, calculate_hartigan_dip, fit_gmm_bimodality
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False
    # Mock the functions for the purpose of testing the test structure if needed
    # But since we are writing the test file, we assume the implementation will be there.
    # For now, we define placeholders to avoid syntax errors if the module is missing
    def assess_bimodality_and_fallback(data, resistance_column, threshold_high=None, threshold_low=None):
        pass
    def calculate_hartigan_dip(data):
        pass
    def fit_gmm_bimodality(data):
        pass


class TestHartiganDipAndGMMBimodality:
    """
    Unit tests for Hartigan's dip test and GMM bimodality assessment.
    These tests verify the statistical methods used to determine if a descriptor
    distribution is bimodal, which informs the choice between binary (Mann-Whitney)
    and continuous (Spearman) statistical tests.
    """

    @pytest.fixture
    def unimodal_data(self):
        """Generate a unimodal normal distribution."""
        np.random.seed(42)
        return np.random.normal(loc=0.0, scale=1.0, size=1000)

    @pytest.fixture
    def bimodal_data(self):
        """Generate a bimodal distribution (mixture of two normals)."""
        np.random.seed(42)
        n1, n2 = 500, 500
        mu1, mu2 = -2.0, 2.0
        sigma1, sigma2 = 1.0, 1.0
        data = np.concatenate([
            np.random.normal(mu1, sigma1, n1),
            np.random.normal(mu2, sigma2, n2)
        ])
        np.random.shuffle(data)
        return data

    @pytest.fixture
    def mock_dataframe(self, unimodal_data, bimodal_data):
        """Create a mock dataframe with test data."""
        df = pd.DataFrame({
            'descriptor_unimodal': unimodal_data,
            'descriptor_bimodal': bimodal_data,
            'resistance_continuous': np.random.rand(len(unimodal_data))
        })
        # Create binary labels based on quartiles for testing
        q_low = df['resistance_continuous'].quantile(0.25)
        q_high = df['resistance_continuous'].quantile(0.75)
        df['resistance_binary'] = df['resistance_continuous'].apply(
            lambda x: 'Low' if x < q_low else ('High' if x > q_high else 'Mid')
        )
        return df

    def test_hartigan_dip_unimodal(self, unimodal_data):
        """
        Test that Hartigan's dip test correctly identifies a unimodal distribution.
        Expected: High p-value (> 0.05), indicating failure to reject unimodality.
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation of calculate_hartigan_dip not yet available")

        # The function should return a dictionary with 'dip_statistic' and 'p_value'
        result = calculate_hartigan_dip(unimodal_data)

        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'dip_statistic' in result, "Result must contain 'dip_statistic'"
        assert 'p_value' in result, "Result must contain 'p_value'"
        assert 0 <= result['dip_statistic'] <= 1, "Dip statistic must be between 0 and 1"
        assert 0 <= result['p_value'] <= 1, "P-value must be between 0 and 1"

        # For a unimodal distribution, p-value should typically be > 0.05
        # However, with small sample sizes or specific parameters, this might vary.
        # We assert the structure and range, and a general expectation for unimodal.
        # Note: dip_test is sensitive, so we just check it runs and returns valid stats.
        assert result['p_value'] > 0.01, f"Unimodal data should have p > 0.01, got {result['p_value']}"

    def test_hartigan_dip_bimodal(self, bimodal_data):
        """
        Test that Hartigan's dip test correctly identifies a bimodal distribution.
        Expected: Low p-value (< 0.05), indicating rejection of unimodality.
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation of calculate_hartigan_dip not yet available")

        result = calculate_hartigan_dip(bimodal_data)

        assert isinstance(result, dict)
        assert 'dip_statistic' in result
        assert 'p_value' in result

        # For a clearly bimodal distribution, p-value should be small
        assert result['p_value'] < 0.1, f"Bimodal data should have p < 0.1, got {result['p_value']}"
        # The dip statistic should be higher than for unimodal
        # (We can't strictly compare without running both, but we check it's non-zero)
        assert result['dip_statistic'] > 0.01, "Dip statistic for bimodal should be significant"

    def test_gmm_bimodality_unimodal(self, unimodal_data):
        """
        Test GMM bimodality assessment on unimodal data.
        Expected: BIC difference favoring 1 component, or low probability of bimodality.
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation of fit_gmm_bimodality not yet available")

        result = fit_gmm_bimodality(unimodal_data)

        assert isinstance(result, dict)
        assert 'bic_1_component' in result
        assert 'bic_2_component' in result
        assert 'bic_difference' in result
        assert 'is_bimodal' in result

        # For unimodal data, 1-component model should have lower BIC (or similar)
        # BIC difference = BIC_2 - BIC_1. If positive, 1-component is better.
        # We expect bic_difference >= 0 for unimodal
        assert result['bic_difference'] >= -2.0, f"Unimodal data should not strongly favor 2 components, diff={result['bic_difference']}"
        # The is_bimodal flag should likely be False
        assert result['is_bimodal'] == False, "Unimodal data should not be flagged as bimodal by GMM"

    def test_gmm_bimodality_bimodal(self, bimodal_data):
        """
        Test GMM bimodality assessment on bimodal data.
        Expected: BIC difference favoring 2 components, or high probability of bimodality.
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation of fit_gmm_bimodality not yet available")

        result = fit_gmm_bimodality(bimodal_data)

        assert isinstance(result, dict)
        assert 'bic_1_component' in result
        assert 'bic_2_component' in result
        assert 'bic_difference' in result
        assert 'is_bimodal' in result

        # For bimodal data, 2-component model should have lower BIC
        # BIC difference = BIC_2 - BIC_1. If negative, 2-component is better.
        assert result['bic_difference'] < 0, f"Bimodal data should favor 2 components, diff={result['bic_difference']}"
        # The is_bimodal flag should likely be True
        assert result['is_bimodal'] == True, "Bimodal data should be flagged as bimodal by GMM"

    def test_assess_bimodality_and_fallback_logic(self, mock_dataframe):
        """
        Test the full assessment pipeline that decides between binary and continuous analysis.
        This test verifies the logic flow:
        1. Check Hartigan's dip test.
        2. If dip test is inconclusive, check GMM.
        3. If neither indicates bimodality, fallback to continuous.
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation of assess_bimodality_and_fallback not yet available")

        # Test with unimodal descriptor
        result_uni = assess_bimodality_and_fallback(
            mock_dataframe,
            'resistance_continuous',
            descriptor_column='descriptor_unimodal'
        )

        assert 'method_used' in result_uni
        assert 'is_bimodal' in result_uni
        assert 'fallback_reason' in result_uni

        # For unimodal data, we expect fallback to continuous
        assert result_uni['method_used'] == 'continuous', f"Unimodal should use continuous, got {result_uni['method_used']}"
        assert result_uni['is_bimodal'] == False

        # Test with bimodal descriptor
        result_bi = assess_bimodality_and_fallback(
            mock_dataframe,
            'resistance_continuous',
            descriptor_column='descriptor_bimodal'
        )

        # For bimodal data, we expect binary method (Mann-Whitney)
        # The exact method name depends on implementation, but it should NOT be 'continuous'
        # or it should indicate bimodality was found.
        assert result_bi['is_bimodal'] == True, "Bimodal descriptor should be detected as bimodal"
        # The method used should be appropriate for bimodal data (e.g., binary)
        # We assume 'binary' is the method name for Mann-Whitney on binary labels
        assert result_bi['method_used'] in ['binary', 'mann_whitney'], f"Bimodal should use binary method, got {result_bi['method_used']}"

    def test_assess_bimodality_handles_missing_data(self):
        """
        Test that the assessment functions handle NaN values gracefully.
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation not yet available")

        data_with_nan = np.array([1.0, 2.0, np.nan, 4.0, 5.0])

        # Both functions should either handle NaNs or raise a clear error
        # We expect them to drop NaNs internally or raise ValueError
        try:
            result_dip = calculate_hartigan_dip(data_with_nan)
            # If it runs, it should return valid results
            assert 'p_value' in result_dip
        except (ValueError, TypeError) as e:
            # Or it might raise an error, which is also acceptable if documented
            assert "NaN" in str(e) or "nan" in str(e) or "missing" in str(e).lower()

        try:
            result_gmm = fit_gmm_bimodality(data_with_nan)
            assert 'bic_difference' in result_gmm
        except (ValueError, TypeError) as e:
            assert "NaN" in str(e) or "nan" in str(e) or "missing" in str(e).lower()

    def test_assess_bimodality_small_sample_size(self):
        """
        Test behavior with very small sample sizes where tests may be unreliable.
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation not yet available")

        small_data = np.array([1.0, 2.0, 3.0])

        # Hartigan's dip test requires a minimum sample size (usually > 5)
        # GMM also needs enough data to fit components
        try:
            result_dip = calculate_hartigan_dip(small_data)
            # If it runs, check structure
            assert 'p_value' in result_dip
        except ValueError as e:
            # Expected: "Sample size too small" or similar
            assert "small" in str(e).lower() or "minimum" in str(e).lower()

        try:
            result_gmm = fit_gmm_bimodality(small_data)
            assert 'bic_difference' in result_gmm
        except ValueError as e:
            assert "small" in str(e).lower() or "minimum" in str(e).lower()

    def test_assess_bimodality_constant_data(self):
        """
        Test behavior with constant data (zero variance).
        """
        if not IMPLEMENTATION_EXISTS:
            pytest.skip("Implementation not yet available")

        constant_data = np.array([5.0, 5.0, 5.0, 5.0])

        # Both tests should handle constant data gracefully
        try:
            result_dip = calculate_hartigan_dip(constant_data)
            # Might return p=1.0 or raise error
            assert 'p_value' in result_dip
        except (ValueError, RuntimeWarning) as e:
            # Expected for zero variance
            pass

        try:
            result_gmm = fit_gmm_bimodality(constant_data)
            assert 'bic_difference' in result_gmm
        except (ValueError, RuntimeWarning) as e:
            # Expected for zero variance
            pass

# Run tests if this file is executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

# Additional helper functions for testing (if needed)
def _generate_bimodal_mixture(n=1000, mu1=-3, mu2=3, sigma1=1, sigma2=1, seed=42):
    """Helper to generate bimodal data for manual verification."""
    np.random.seed(seed)
    n1 = n // 2
    n2 = n - n1
    data1 = np.random.normal(mu1, sigma1, n1)
    data2 = np.random.normal(mu2, sigma2, n2)
    return np.concatenate([data1, data2])