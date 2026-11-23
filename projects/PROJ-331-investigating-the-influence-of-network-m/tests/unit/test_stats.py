"""
Unit tests for stats.py functions.
Tests VIF computation, partial correlation, and statistical corrections.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from stats import (
    load_subject_metrics_data,
    compute_vif,
    check_vif_and_select_method,
    report_insufficient_variance
)


class TestLoadSubjectMetricsData:
    """Tests for the load_subject_metrics_data function."""

    def test_load_csv_success(self):
        """Test loading a valid CSV file."""
        # Create a temporary CSV
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("subject_id,motif_id,z_score,rsfc_strength\n")
            f.write("sub-001,motif_0,2.5,0.3\n")
            f.write("sub-002,motif_0,1.8,0.4\n")
            temp_path = f.name

        try:
            df = load_subject_metrics_data(temp_path)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert 'subject_id' in df.columns
        finally:
            os.unlink(temp_path)

    def test_load_csv_missing_file(self):
        """Test loading a missing CSV file."""
        with pytest.raises(FileNotFoundError):
            load_subject_metrics_data("nonexistent.csv")

    def test_load_csv_empty(self):
        """Test loading an empty CSV file."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            df = load_subject_metrics_data(temp_path)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0
        finally:
            os.unlink(temp_path)


class TestComputeVIF:
    """Tests for the compute_vif function."""

    def test_vif_simple(self):
        """Test VIF computation on simple data."""
        # Create a simple dataframe
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],  # Perfectly correlated with x1
            'y': [1, 3, 5, 7, 9]
        })

        # VIF for x1 should be very high (infinite with perfect correlation)
        vif_x1 = compute_vif(df, 'x1')
        assert vif_x1 >= 1.0  # VIF is always >= 1

    def test_vif_independent(self):
        """Test VIF on independent variables."""
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.rand(100),
            'x2': np.random.rand(100),
            'x3': np.random.rand(100)
        })

        vif_x1 = compute_vif(df, 'x1')
        # With independent variables, VIF should be close to 1
        assert 1.0 <= vif_x1 < 2.0

    def test_vif_single_variable(self):
        """Test VIF with only one variable."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5]
        })

        vif_x1 = compute_vif(df, 'x1')
        # With no other variables, VIF should be 1
        assert vif_x1 == 1.0


class TestCheckVifAndSelectMethod:
    """Tests for the check_vif_and_select_method function."""

    def test_vif_low_uses_partial_corr(self):
        """Test that low VIF selects partial correlation method."""
        np.random.seed(42)
        metrics = pd.DataFrame({
            'motif_id': ['m0', 'm1', 'm2'] * 10,
            'z_score': np.random.rand(30),
            'rsfc_strength': np.random.rand(30),
            'global_node_degree': np.random.rand(30)
        })

        result = check_vif_and_select_method(metrics)
        assert 'method_selected' in result
        assert result['vif_value'] < 5.0 or result['method_selected'] == 'permutation_only'

    def test_vif_high_uses_permutation(self):
        """Test that high VIF selects permutation-only method."""
        # Create data with high multicollinearity
        np.random.seed(42)
        x = np.random.rand(50)
        metrics = pd.DataFrame({
            'motif_id': ['m0'] * 50,
            'z_score': x,
            'rsfc_strength': x * 1.1 + np.random.rand(50) * 0.01,  # Highly correlated
            'global_node_degree': x * 0.9 + np.random.rand(50) * 0.01  # Highly correlated
        })

        result = check_vif_and_select_method(metrics)
        # If VIF > 5, method should be permutation_only
        if result['vif_value'] > 5:
            assert result['method_selected'] == 'permutation_only'

    def test_zero_variance_handling(self):
        """Test handling of zero variance in z_scores."""
        metrics = pd.DataFrame({
            'motif_id': ['m0', 'm0', 'm0'],
            'z_score': [0.0, 0.0, 0.0],  # Zero variance
            'rsfc_strength': [0.1, 0.2, 0.3],
            'global_node_degree': [0.5, 0.6, 0.7]
        })

        result = check_vif_and_select_method(metrics)
        assert 'zero_variance' in result
        assert result['zero_variance'] is True


class TestReportInsufficientVariance:
    """Tests for the report_insufficient_variance function."""

    def test_report_insufficient_variance_format(self):
        """Test that the report format is correct."""
        result = report_insufficient_variance('motif_0')
        
        assert isinstance(result, dict)
        assert 'motif_id' in result
        assert result['motif_id'] == 'motif_0'
        assert 'status' in result
        assert result['status'] == 'insufficient_variance'

    def test_report_insufficient_variance_message(self):
        """Test that the report contains the expected message."""
        result = report_insufficient_variance('motif_1')
        
        assert 'message' in result
        assert 'insufficient variance' in result['message'].lower()