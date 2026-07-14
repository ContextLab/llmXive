"""
Unit tests for T017: output_cleaned_dataset.py

Tests the merge, filter, and verification logic.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.output_cleaned_dataset import merge_and_filter, verify_retention

class TestMergeAndFilter:
    
    def test_merge_alpha_with_metadata(self):
        """Test merging alpha metrics with metadata on sample_id."""
        alpha_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'shannon': [3.5, 4.2, 3.8],
            'simpson': [0.9, 0.95, 0.92]
        })
        
        metadata_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'phq9': [10, 5, 15],
            'gad7': [8, 4, 12],
            'age': [30, 45, 28]
        })
        
        result = merge_and_filter(alpha_df, None, metadata_df)
        
        assert result is not None
        assert len(result) == 3
        assert 'phq9' in result.columns
        assert 'gad7' in result.columns
        assert 'shannon' in result.columns

    def test_filter_missing_phq9(self):
        """Test that rows with missing PHQ-9 are filtered out."""
        alpha_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'shannon': [3.5, 4.2, 3.8],
            'simpson': [0.9, 0.95, 0.92]
        })
        
        metadata_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'phq9': [10, np.nan, 15],
            'gad7': [8, 4, 12]
        })
        
        result = merge_and_filter(alpha_df, None, metadata_df)
        
        assert result is not None
        assert len(result) == 2
        # S2 should be filtered out
        assert 'S2' not in result['sample_id'].values

    def test_filter_missing_diversity(self):
        """Test that rows with missing diversity metrics are filtered out."""
        alpha_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'shannon': [3.5, np.nan, 3.8],
            'simpson': [0.9, 0.95, 0.92]
        })
        
        metadata_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'phq9': [10, 5, 15],
            'gad7': [8, 4, 12]
        })
        
        result = merge_and_filter(alpha_df, None, metadata_df)
        
        assert result is not None
        assert len(result) == 2
        # S2 should be filtered out
        assert 'S2' not in result['sample_id'].values

    def test_inner_join_behavior(self):
        """Test that only samples present in both datasets are kept."""
        alpha_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'shannon': [3.5, 4.2, 3.8]
        })
        
        metadata_df = pd.DataFrame({
            'sample_id': ['S2', 'S3', 'S4'],
            'phq9': [5, 15, 8]
        })
        
        result = merge_and_filter(alpha_df, None, metadata_df)
        
        assert result is not None
        assert len(result) == 2
        assert set(result['sample_id'].values) == {'S2', 'S3'}

    def test_empty_result_on_no_overlap(self):
        """Test that empty result is returned when no samples overlap."""
        alpha_df = pd.DataFrame({
            'sample_id': ['S1', 'S2'],
            'shannon': [3.5, 4.2]
        })
        
        metadata_df = pd.DataFrame({
            'sample_id': ['S3', 'S4'],
            'phq9': [5, 15]
        })
        
        result = merge_and_filter(alpha_df, None, metadata_df)
        
        assert result is None or len(result) == 0

class TestVerifyRetention:
    
    def test_passes_80_percent_100_rows(self):
        """Test verification passes with >80% retention and >100 rows."""
        clean_df = pd.DataFrame({'col': range(150)})
        original = 180
        
        passed, msg = verify_retention(clean_df, original)
        
        assert passed is True
        assert "passed" in msg.lower()

    def test_fails_low_retention(self):
        """Test verification fails with <80% retention."""
        clean_df = pd.DataFrame({'col': range(50)})
        original = 100
        
        passed, msg = verify_retention(clean_df, original)
        
        assert passed is False
        assert "retention" in msg.lower()

    def test_fails_low_rows(self):
        """Test verification fails with <100 rows."""
        clean_df = pd.DataFrame({'col': range(50)})
        original = 200  # 25% retention, but also <100 rows
        
        passed, msg = verify_retention(clean_df, original)
        
        assert passed is False
        assert "100" in msg or "rows" in msg.lower()

    def test_zero_original_count(self):
        """Test verification fails with zero original count."""
        clean_df = pd.DataFrame({'col': range(100)})
        original = 0
        
        passed, msg = verify_retention(clean_df, original)
        
        assert passed is False
        assert "0" in msg
