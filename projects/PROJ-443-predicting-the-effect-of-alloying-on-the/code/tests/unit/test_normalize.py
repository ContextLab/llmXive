"""
Unit tests for normalization logic in src/data/normalize.py.

Tests verify:
1. Composition sums are normalized to 1.0
2. Zero-sum compositions are handled gracefully
3. Already-normalized compositions are left unchanged
4. Logging of adjustments works correctly
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import logging
from io import StringIO

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.normalize import (
    get_composition_columns,
    normalize_composition_row,
    normalize_dataframe,
    main
)
from utils.validators import ValidationError

class TestGetCompositionColumns:
    """Test identification of composition columns."""
    
    def test_identifies_composition_columns(self):
        """Should correctly identify columns starting with 'comp_'."""
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'comp_Fe': [0.2, 0.3],
            'comp_Co': [0.3, 0.2],
            'comp_Ni': [0.5, 0.5],
            'other_col': ['a', 'b']
        })
        
        comp_cols = get_composition_columns(df)
        
        assert len(comp_cols) == 3
        assert set(comp_cols) == {'comp_Fe', 'comp_Co', 'comp_Ni'}
    
    def test_empty_dataframe(self):
        """Should return empty list for empty DataFrame."""
        df = pd.DataFrame()
        
        comp_cols = get_composition_columns(df)
        
        assert comp_cols == []
    
    def test_no_composition_columns(self):
        """Should return empty list when no composition columns exist."""
        df = pd.DataFrame({
            'sample_id': [1, 2],
            'bulk_modulus': [100, 200]
        })
        
        comp_cols = get_composition_columns(df)
        
        assert comp_cols == []

class TestNormalizeCompositionRow:
    """Test normalization of individual rows."""
    
    def test_normalize_unnormalized_composition(self):
        """Should normalize composition to sum=1.0."""
        row = pd.Series({
            'sample_id': 'test_1',
            'comp_Fe': 0.4,
            'comp_Co': 0.6,
            'comp_Ni': 0.0
        })
        comp_cols = ['comp_Fe', 'comp_Co', 'comp_Ni']
        
        # Create logger
        logger = logging.getLogger('test')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(StringIO())
        logger.addHandler(handler)
        
        normalized_row, info = normalize_composition_row(row, comp_cols, logger)
        
        assert abs(normalized_row['comp_Fe'] - 0.4) < 1e-6
        assert abs(normalized_row['comp_Co'] - 0.6) < 1e-6
        assert abs(normalized_row['comp_Ni'] - 0.0) < 1e-6
        assert info['adjusted'] is True
        assert abs(info['original_sum'] - 1.0) < 1e-6  # Already sums to 1.0 in this case
    
    def test_normalize_composition_that_needs_adjustment(self):
        """Should adjust composition that doesn't sum to 1.0."""
        row = pd.Series({
            'sample_id': 'test_2',
            'comp_Fe': 0.3,
            'comp_Co': 0.4,
            'comp_Ni': 0.2  # Sum = 0.9
        })
        comp_cols = ['comp_Fe', 'comp_Co', 'comp_Ni']
        
        logger = logging.getLogger('test')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(StringIO())
        logger.addHandler(handler)
        
        normalized_row, info = normalize_composition_row(row, comp_cols, logger)
        
        # Check that sum is now 1.0
        total = normalized_row['comp_Fe'] + normalized_row['comp_Co'] + normalized_row['comp_Ni']
        assert abs(total - 1.0) < 1e-6
        
        # Check that relative proportions are preserved
        assert normalized_row['comp_Fe'] == pytest.approx(0.3 / 0.9)
        assert normalized_row['comp_Co'] == pytest.approx(0.4 / 0.9)
        assert normalized_row['comp_Ni'] == pytest.approx(0.2 / 0.9)
        
        assert info['adjusted'] is True
        assert info['original_sum'] == 0.9
    
    def test_zero_sum_composition(self):
        """Should handle zero-sum composition gracefully."""
        row = pd.Series({
            'sample_id': 'test_3',
            'comp_Fe': 0.0,
            'comp_Co': 0.0,
            'comp_Ni': 0.0
        })
        comp_cols = ['comp_Fe', 'comp_Co', 'comp_Ni']
        
        logger = logging.getLogger('test')
        logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler(StringIO())
        logger.addHandler(handler)
        
        normalized_row, info = normalize_composition_row(row, comp_cols, logger)
        
        # Values should remain unchanged
        assert normalized_row['comp_Fe'] == 0.0
        assert normalized_row['comp_Co'] == 0.0
        assert normalized_row['comp_Ni'] == 0.0
        assert info['adjusted'] is False
        assert info['original_sum'] == 0.0

class TestNormalizeDataFrame:
    """Test DataFrame-level normalization."""
    
    def test_normalize_dataframe(self):
        """Should normalize all rows in a DataFrame."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2', 's3'],
            'comp_Fe': [0.3, 0.4, 0.2],
            'comp_Co': [0.4, 0.3, 0.3],
            'comp_Ni': [0.2, 0.2, 0.4]  # All rows sum to 0.9
        })
        
        logger = logging.getLogger('test')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(StringIO())
        logger.addHandler(handler)
        
        normalized_df, stats = normalize_dataframe(df, logger)
        
        # Check that all rows sum to 1.0
        for idx, row in normalized_df.iterrows():
            total = row['comp_Fe'] + row['comp_Co'] + row['comp_Ni']
            assert abs(total - 1.0) < 1e-6
        
        assert stats['total_samples'] == 3
        assert stats['normalized_samples'] == 3
        assert stats['verification_passed'] is True
    
    def test_mixed_normalization_needed(self):
        """Should handle DataFrame with mix of normalized and unnormalized rows."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2', 's3'],
            'comp_Fe': [0.5, 0.3, 0.4],
            'comp_Co': [0.5, 0.4, 0.3],  # s1 sums to 1.0, others sum to 0.7 and 0.7
            'comp_Ni': [0.0, 0.0, 0.0]
        })
        
        logger = logging.getLogger('test')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(StringIO())
        logger.addHandler(handler)
        
        normalized_df, stats = normalize_dataframe(df, logger)
        
        # Check sums
        for idx, row in normalized_df.iterrows():
            total = row['comp_Fe'] + row['comp_Co'] + row['comp_Ni']
            assert abs(total - 1.0) < 1e-6
        
        assert stats['total_samples'] == 3
        assert stats['normalized_samples'] == 2  # Only s2 and s3 needed adjustment
    
    def test_missing_composition_columns(self):
        """Should raise ValidationError when no composition columns found."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'bulk_modulus': [100, 200]
        })
        
        logger = logging.getLogger('test')
        
        with pytest.raises(ValidationError) as exc_info:
            normalize_dataframe(df, logger)
        
        assert "No composition columns found" in str(exc_info.value)
    
    def test_preserves_non_composition_columns(self):
        """Should preserve non-composition columns during normalization."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'bulk_modulus': [150, 200],
            'comp_Fe': [0.3, 0.4],
            'comp_Co': [0.4, 0.3],
            'comp_Ni': [0.2, 0.2]
        })
        
        logger = logging.getLogger('test')
        
        normalized_df, stats = normalize_dataframe(df, logger)
        
        # Check that non-composition columns are preserved
        assert 'sample_id' in normalized_df.columns
        assert 'bulk_modulus' in normalized_df.columns
        assert list(normalized_df['sample_id']) == ['s1', 's2']
        assert list(normalized_df['bulk_modulus']) == [150, 200]

class TestNormalizationEdgeCases:
    """Test edge cases in normalization."""
    
    def test_nan_values_in_composition(self):
        """Should handle NaN values in composition columns."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'comp_Fe': [0.3, np.nan],
            'comp_Co': [0.4, 0.5],
            'comp_Ni': [np.nan, 0.5]
        })
        
        logger = logging.getLogger('test')
        
        # This should not crash, but may produce unexpected results
        # depending on how nansum handles the data
        normalized_df, stats = normalize_dataframe(df, logger)
        
        # Just verify it runs without error
        assert normalized_df is not None
    
    def test_single_element_composition(self):
        """Should handle compositions with only one element."""
        df = pd.DataFrame({
            'sample_id': ['s1'],
            'comp_Fe': [1.5],  # Sum > 1.0
            'comp_Co': [0.0],
            'comp_Ni': [0.0]
        })
        
        logger = logging.getLogger('test')
        
        normalized_df, stats = normalize_dataframe(df, logger)
        
        # Should normalize to 1.0
        assert normalized_df['comp_Fe'].iloc[0] == pytest.approx(1.0)
        assert normalized_df['comp_Co'].iloc[0] == pytest.approx(0.0)
        assert normalized_df['comp_Ni'].iloc[0] == pytest.approx(0.0)
    
    def test_very_small_composition_values(self):
        """Should handle very small composition values."""
        df = pd.DataFrame({
            'sample_id': ['s1'],
            'comp_Fe': [1e-10],
            'comp_Co': [1e-10],
            'comp_Ni': [1e-10]
        })
        
        logger = logging.getLogger('test')
        
        normalized_df, stats = normalize_dataframe(df, logger)
        
        # Should normalize to 1.0
        total = normalized_df['comp_Fe'].iloc[0] + normalized_df['comp_Co'].iloc[0] + normalized_df['comp_Ni'].iloc[0]
        assert abs(total - 1.0) < 1e-6