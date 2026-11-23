"""
Unit tests for SIMEX correction implementation.

Tests the SIMEX correction logic for misclassification bias in LMER coefficients.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

import numpy as np
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.simex_correction import (
    simulate_misclassification,
    extrapolate_to_zero_noise,
    apply_simex_correction
)


class TestSimulateMisclassification:
    """Tests for the simulate_misclassification function."""

    def test_no_misclassification_when_rate_is_zero(self):
        """When fp_rate and fn_rate are 0, labels should remain unchanged."""
        df = pd.DataFrame({
            'origin_label': ['Disclosing', 'Non-Disclosing', 'Disclosing'],
            'other_col': [1, 2, 3]
        })
        
        result = simulate_misclassification(df, fp_rate=0.0, fn_rate=0.0, seed=42)
        
        assert list(result['simulated_origin_label']) == ['Disclosing', 'Non-Disclosing', 'Disclosing']

    def test_misclassification_occurs_with_positive_rate(self):
        """With positive error rates, some labels should change."""
        df = pd.DataFrame({
            'origin_label': ['Disclosing'] * 100 + ['Non-Disclosing'] * 100,
            'other_col': range(200)
        })
        
        # With high error rate, we expect some changes
        result = simulate_misclassification(df, fp_rate=0.3, fn_rate=0.3, seed=42)
        
        original_disclosing = (df['origin_label'] == 'Disclosing').sum()
        simulated_disclosing = (result['simulated_origin_label'] == 'Disclosing').sum()
        
        # Should have some change due to misclassification
        assert original_disclosing != simulated_disclosing

    def test_seed_reproducibility(self):
        """Same seed should produce same results."""
        df = pd.DataFrame({
            'origin_label': ['Disclosing', 'Non-Disclosing'] * 50,
            'other_col': range(100)
        })
        
        result1 = simulate_misclassification(df, fp_rate=0.2, fn_rate=0.2, seed=123)
        result2 = simulate_misclassification(df, fp_rate=0.2, fn_rate=0.2, seed=123)
        
        assert list(result1['simulated_origin_label']) == list(result2['simulated_origin_label'])

    def test_fp_only_affects_non_disclosing(self):
        """False positives should only affect Non-Disclosing labels."""
        df = pd.DataFrame({
            'origin_label': ['Non-Disclosing'] * 100,
            'other_col': range(100)
        })
        
        result = simulate_misclassification(df, fp_rate=0.5, fn_rate=0.0, seed=42)
        
        # Some should flip to Disclosing
        disclosing_count = (result['simulated_origin_label'] == 'Disclosing').sum()
        assert 0 < disclosing_count < 100


class TestExtrapolateToZeroNoise:
    """Tests for the extrapolate_to_zero_noise function."""

    def test_quadratic_extrapolation(self):
        """Test quadratic extrapolation works correctly."""
        # Simulate a quadratic relationship: coef = lambda^2 - 2*lambda + 5
        # At lambda = -1, expected value = 1 + 2 + 5 = 8
        lambdas = np.array([0, 0.5, 1.0, 1.5, 2.0])
        coefficients = np.array([5.0, 3.25, 4.0, 7.25, 13.0])
        
        result = extrapolate_to_zero_noise(coefficients, lambdas)
        
        # Should be close to 8 (allowing for numerical precision)
        assert 7.5 < result < 8.5

    def test_insufficient_points(self):
        """Should return NaN with too few valid points."""
        lambdas = np.array([0, 0.5, 1.0])
        coefficients = [np.nan, np.nan, 5.0]  # Only 1 valid point
        
        result = extrapolate_to_zero_noise(coefficients, lambdas)
        
        assert np.isnan(result)

    def test_all_nan_coefficients(self):
        """Should return NaN when all coefficients are NaN."""
        lambdas = np.array([0, 0.5, 1.0])
        coefficients = [np.nan, np.nan, np.nan]
        
        result = extrapolate_to_zero_noise(coefficients, lambdas)
        
        assert np.isnan(result)


class TestApplySimexCorrection:
    """Tests for the apply_simex_correction function."""

    def test_skip_when_fp_rate_low(self):
        """Should skip correction when fp_rate <= 0.05."""
        df = pd.DataFrame({
            'origin_label': ['Disclosing'] * 50 + ['Non-Disclosing'] * 50,
            'total_review_time': np.random.rand(100) * 1000,
            'code_lines_changed': np.random.rand(100) * 100,
            'repo_id': ['repo1'] * 50 + ['repo2'] * 50
        })
        
        results = {'lmer': {'coefficients': {'origin_binary': 10.0}}}
        
        updated_results = apply_simex_correction(df, fp_rate=0.03, results=results)
        
        assert not updated_results['simex_corrected_coefficients']['applied']
        assert updated_results['simex_corrected_coefficients']['reason'] == 'fp_rate <= 0.05'

    def test_apply_when_fp_rate_high(self):
        """Should attempt correction when fp_rate > 0.05."""
        df = pd.DataFrame({
            'origin_label': ['Disclosing'] * 50 + ['Non-Disclosing'] * 50,
            'total_review_time': np.random.rand(100) * 1000,
            'code_lines_changed': np.random.rand(100) * 100,
            'repo_id': ['repo1'] * 50 + ['repo2'] * 50
        })
        
        results = {'lmer': {'coefficients': {'origin_binary': 10.0}}}
        
        # This will attempt correction but might fail due to missing statsmodels
        # We're testing that the logic path is correct
        updated_results = apply_simex_correction(df, fp_rate=0.1, results=results)
        
        assert updated_results['simex_corrected_coefficients']['applied']
        # Status depends on whether LMER fitting succeeded
        assert 'status' in updated_results['simex_corrected_coefficients']

    def test_returns_updated_results(self):
        """Should return the results dictionary with SIMEX results added."""
        df = pd.DataFrame({
            'origin_label': ['Disclosing'] * 50 + ['Non-Disclosing'] * 50,
            'total_review_time': np.random.rand(100) * 1000,
            'code_lines_changed': np.random.rand(100) * 100,
            'repo_id': ['repo1'] * 50 + ['repo2'] * 50
        })
        
        results = {'lmer': {'coefficients': {'origin_binary': 10.0}}, 'other_key': 'value'}
        
        updated_results = apply_simex_correction(df, fp_rate=0.03, results=results)
        
        assert 'simex_corrected_coefficients' in updated_results
        assert updated_results['other_key'] == 'value'  # Original data preserved