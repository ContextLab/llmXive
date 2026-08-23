"""
Unit tests for stats.py functions.
Tests VIF calculation, method selection, and insufficient variance reporting.
"""
import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from stats import compute_vif, check_vif_and_select_method, report_insufficient_variance
from config import ensure_dirs


class TestComputeVIF:
    """Tests for the compute_vif function."""

    def test_vif_single_variable(self):
        """VIF for a single variable should be 1.0 (no multicollinearity)."""
        # Create a simple dataframe with one predictor
        data = pd.DataFrame({
            'global_node_degree': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        vif = compute_vif(data, 'global_node_degree')
        assert vif == 1.0

    def test_vif_perfect_collinearity(self):
        """VIF should be infinite (or very large) for perfect collinearity."""
        # Create data where one variable is a perfect linear combination of another
        data = pd.DataFrame({
            'var1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'var2': [2.0, 4.0, 6.0, 8.0, 10.0]  # var2 = 2 * var1
        })
        # We test with var1, but var2 is perfectly collinear
        vif = compute_vif(data, 'var1')
        assert vif >= 1000.0  # Should be very large

    def test_vif_no_collinearity(self):
        """VIF should be close to 1.0 when variables are uncorrelated."""
        # Create data with low correlation between variables
        np.random.seed(42)
        data = pd.DataFrame({
            'var1': np.random.randn(100),
            'var2': np.random.randn(100),
            'var3': np.random.randn(100)
        })
        vif = compute_vif(data, 'var1')
        assert 0.5 < vif < 2.0  # Should be close to 1

    def test_vif_with_constant(self):
        """VIF should handle constant variables appropriately."""
        data = pd.DataFrame({
            'var1': [1.0, 1.0, 1.0, 1.0, 1.0],
            'var2': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        # This should raise an error or return a high VIF due to singularity
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            compute_vif(data, 'var1')


class TestCheckVifAndSelectMethod:
    """Tests for the check_vif_and_select_method function."""

    def test_low_vif_selects_partial_correlation(self):
        """Should select partial correlation when VIF is low."""
        # Create mock metrics with low variance in z-scores and low VIF
        data = pd.DataFrame({
            'motif_id': ['motif_1'] * 50,
            'z_score': np.random.randn(50),
            'rsfc_strength': np.random.randn(50),
            'global_node_degree': np.random.randn(50)
        })
        result = check_vif_and_select_method(data)
        assert result['method_selected'] in ['partial_correlation', 'both']
        assert result['vif_value'] < 5.0

    def test_high_vif_selects_permutation_only(self):
        """Should select permutation-only when VIF is high."""
        # Create data with high collinearity
        np.random.seed(42)
        base = np.random.randn(50)
        data = pd.DataFrame({
            'motif_id': ['motif_1'] * 50,
            'z_score': base,
            'rsfc_strength': base,  # Perfect correlation
            'global_node_degree': base * 2  # Also perfectly correlated
        })
        result = check_vif_and_select_method(data)
        assert result['method_selected'] == 'permutation_only'
        assert result['vif_value'] >= 5.0

    def test_zero_variance_flag(self):
        """Should detect zero variance in z-scores."""
        data = pd.DataFrame({
            'motif_id': ['motif_1'] * 50,
            'z_score': [0.0] * 50,  # Zero variance
            'rsfc_strength': np.random.randn(50),
            'global_node_degree': np.random.randn(50)
        })
        result = check_vif_and_select_method(data)
        assert result['zero_variance'] is True

    def test_nonzero_variance_flag(self):
        """Should not flag zero variance when there is variance."""
        data = pd.DataFrame({
            'motif_id': ['motif_1'] * 50,
            'z_score': np.random.randn(50),
            'rsfc_strength': np.random.randn(50),
            'global_node_degree': np.random.randn(50)
        })
        result = check_vif_and_select_method(data)
        assert result['zero_variance'] is False

    def test_output_schema(self):
        """Should return the correct schema."""
        data = pd.DataFrame({
            'motif_id': ['motif_1'] * 50,
            'z_score': np.random.randn(50),
            'rsfc_strength': np.random.randn(50),
            'global_node_degree': np.random.randn(50)
        })
        result = check_vif_and_select_method(data)
        assert 'zero_variance' in result
        assert 'vif_value' in result
        assert 'method_selected' in result
        assert isinstance(result['zero_variance'], bool)
        assert isinstance(result['vif_value'], float)
        assert isinstance(result['method_selected'], str)


class TestReportInsufficientVariance:
    """Tests for the report_insufficient_variance function."""

    def test_returns_correct_message(self):
        """Should return a message indicating insufficient variance."""
        result = report_insufficient_variance('motif_1')
        assert 'insufficient variance' in result.lower()
        assert 'motif_1' in result

    def test_returns_dict(self):
        """Should return a dictionary with the expected structure."""
        result = report_insufficient_variance('motif_1')
        assert isinstance(result, dict)
        assert 'motif_id' in result
        assert 'message' in result
        assert 'status' in result
        assert result['status'] == 'insufficient_variance'

    def test_various_motif_ids(self):
        """Should handle various motif IDs correctly."""
        for motif_id in ['motif_1', 'motif_2', '3-node-motif-A', 'test-motif']:
            result = report_insufficient_variance(motif_id)
            assert result['motif_id'] == motif_id
            assert 'insufficient variance' in result['message'].lower()
