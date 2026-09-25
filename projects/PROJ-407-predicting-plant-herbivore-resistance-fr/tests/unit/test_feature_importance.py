"""
Unit tests for T026: Feature Importance Table Generation.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from pathlib import Path

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from feature_importance import (
    extract_metabolite_columns,
    calculate_correlations,
    build_feature_importance_table
)


class TestExtractMetaboliteColumns:
    """Tests for extract_metabolite_columns function."""

    def test_standard_metabolite_columns(self):
        """Test extraction of standard metabolite_* columns."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'metabolite_A': [1.0, 2.0, 3.0],
            'metabolite_B': [4.0, 5.0, 6.0],
            'resistance': [10, 20, 30]
        })
        
        result = extract_metabolite_columns(df)
        
        assert 'metabolite_A' in result
        assert 'metabolite_B' in result
        assert 'sample_id' not in result
        assert 'resistance' not in result

    def test_alternative_naming(self):
        """Test extraction of metabolites with alternative naming."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'metab_compound_1': [1.0, 2.0, 3.0],
            'metab_compound_2': [4.0, 5.0, 6.0],
            'resistance': [10, 20, 30]
        })
        
        result = extract_metabolite_columns(df)
        
        assert len(result) == 2
        assert 'metab_compound_1' in result
        assert 'metab_compound_2' in result

    def test_no_metabolite_columns(self):
        """Test error handling when no metabolite columns are found."""
        df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'resistance': [10, 20, 30]
        })
        
        with pytest.raises(ValueError, match="No metabolite columns found"):
            extract_metabolite_columns(df)


class TestCalculateCorrelations:
    """Tests for calculate_correlations function."""

    def test_perfect_correlation(self):
        """Test calculation with perfect positive correlation."""
        df = pd.DataFrame({
            'metabolite_A': [1.0, 2.0, 3.0, 4.0, 5.0],
            'resistance': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        result = calculate_correlations(df, ['metabolite_A'], target_col='resistance')
        
        assert 'metabolite_A' in result
        assert result['metabolite_A']['correlation'] == pytest.approx(1.0, abs=1e-6)
        assert result['metabolite_A']['p_value'] < 0.05

    def test_negative_correlation(self):
        """Test calculation with negative correlation."""
        df = pd.DataFrame({
            'metabolite_A': [5.0, 4.0, 3.0, 2.0, 1.0],
            'resistance': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        result = calculate_correlations(df, ['metabolite_A'], target_col='resistance')
        
        assert result['metabolite_A']['correlation'] == pytest.approx(-1.0, abs=1e-6)
        assert result['metabolite_A']['p_value'] < 0.05

    def test_no_correlation(self):
        """Test calculation with no correlation."""
        np.random.seed(42)
        df = pd.DataFrame({
            'metabolite_A': np.random.randn(100),
            'resistance': np.random.randn(100)
        })
        
        result = calculate_correlations(df, ['metabolite_A'], target_col='resistance')
        
        # Correlation should be close to 0, p-value should be high
        assert abs(result['metabolite_A']['correlation']) < 0.2
        assert result['metabolite_A']['p_value'] > 0.05

    def test_insufficient_data(self):
        """Test handling of insufficient data points."""
        df = pd.DataFrame({
            'metabolite_A': [1.0, 2.0],
            'resistance': [10, 20]
        })
        
        result = calculate_correlations(df, ['metabolite_A'], target_col='resistance')
        
        assert np.isnan(result['metabolite_A']['correlation'])
        assert np.isnan(result['metabolite_A']['p_value'])


class TestBuildFeatureImportanceTable:
    """Tests for build_feature_importance_table function."""

    def test_basic_table_creation(self):
        """Test basic table creation with mock model."""
        # Create mock model
        model = Mock()
        model.feature_importances_ = np.array([0.5, 0.3, 0.2])
        
        metabolite_cols = ['metabolite_A', 'metabolite_B', 'metabolite_C']
        correlations = {
            'metabolite_A': {'correlation': 0.8, 'p_value': 0.001},
            'metabolite_B': {'correlation': -0.5, 'p_value': 0.05},
            'metabolite_C': {'correlation': 0.1, 'p_value': 0.8}
        }
        
        result = build_feature_importance_table(model, metabolite_cols, correlations)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == ['metabolite_name', 'importance_score', 
                                       'unadjusted_p_value', 'correlation_coefficient']
        
        # Check values
        assert result.iloc[0]['metabolite_name'] == 'metabolite_A'
        assert result.iloc[0]['importance_score'] == 0.5
        assert result.iloc[0]['unadjusted_p_value'] == 0.001
        assert result.iloc[0]['correlation_coefficient'] == 0.8

    def test_mismatched_feature_counts(self):
        """Test handling of mismatched feature counts between model and data."""
        model = Mock()
        model.feature_importances_ = np.array([0.5, 0.3])  # Only 2 features
        
        metabolite_cols = ['metabolite_A', 'metabolite_B', 'metabolite_C']  # 3 columns
        correlations = {
            'metabolite_A': {'correlation': 0.8, 'p_value': 0.001},
            'metabolite_B': {'correlation': -0.5, 'p_value': 0.05},
            'metabolite_C': {'correlation': 0.1, 'p_value': 0.8}
        }
        
        # Should not raise, but truncate to minimum length
        result = build_feature_importance_table(model, metabolite_cols, correlations)
        
        assert len(result) == 2
        assert 'metabolite_C' not in result['metabolite_name'].values