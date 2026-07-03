"""
Integration tests for data consolidation logic (T013).

Tests that:
1. Scrubbed timeseries and behavioral data can be merged
2. Output file is created with correct schema
3. Subject-level statistics are calculated correctly
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.consolidate_data import (
    load_scrubbed_timeseries,
    load_behavioral_scores,
    merge_datasets,
    validate_consolidated_data
)

class TestDataConsolidation:
    """Test data consolidation logic."""

    def test_merge_datasets_basic(self, tmp_path):
        """Test basic dataset merging functionality."""
        # Create mock timeseries data
        timeseries_data = {
            'subject_id': ['sub-01', 'sub-01', 'sub-02', 'sub-02'],
            'timepoint': [1, 2, 1, 2],
            'region': ['A', 'A', 'B', 'B'],
            'signal': [0.5, 0.6, 0.7, 0.8]
        }
        timeseries_df = pd.DataFrame(timeseries_data)
        
        # Create mock behavioral data
        behavioral_data = {
            'subject_id': ['sub-01', 'sub-02'],
            'accuracy': [0.85, 0.90]
        }
        behavioral_df = pd.DataFrame(behavioral_data)
        
        # Merge datasets
        merged_df = merge_datasets(timeseries_df, behavioral_df)
        
        # Assertions
        assert len(merged_df) == 2
        assert 'subject_id' in merged_df.columns
        assert 'accuracy' in merged_df.columns
        assert 'n_timepoints' in merged_df.columns
        assert 'n_regions' in merged_df.columns
        
        # Check values
        assert merged_df.loc[merged_df['subject_id'] == 'sub-01', 'accuracy'].values[0] == 0.85
        assert merged_df.loc[merged_df['subject_id'] == 'sub-01', 'n_timepoints'].values[0] == 2

    def test_merge_datasets_missing_subjects(self, tmp_path):
        """Test merging when some subjects are missing in one dataset."""
        # Create timeseries data with subjects 01, 02
        timeseries_data = {
            'subject_id': ['sub-01', 'sub-01', 'sub-02', 'sub-02'],
            'timepoint': [1, 2, 1, 2],
            'region': ['A', 'A', 'B', 'B'],
            'signal': [0.5, 0.6, 0.7, 0.8]
        }
        timeseries_df = pd.DataFrame(timeseries_data)
        
        # Create behavioral data with only subject 01
        behavioral_data = {
            'subject_id': ['sub-01'],
            'accuracy': [0.85]
        }
        behavioral_df = pd.DataFrame(behavioral_data)
        
        # Merge datasets
        merged_df = merge_datasets(timeseries_df, behavioral_df)
        
        # Should only include subjects present in both
        assert len(merged_df) == 1
        assert 'sub-01' in merged_df['subject_id'].values

    def test_validate_consolidated_data(self, tmp_path):
        """Test validation of consolidated dataset."""
        valid_df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02'],
            'accuracy': [0.85, 0.90]
        })
        
        assert validate_consolidated_data(valid_df) is True

    def test_validate_consolidated_data_missing_columns(self, tmp_path):
        """Test validation fails with missing columns."""
        invalid_df = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02'],
            'other_column': [0.85, 0.90]
        })
        
        assert validate_consolidated_data(invalid_df) is False

    def test_validate_consolidated_data_empty(self, tmp_path):
        """Test validation fails with empty dataframe."""
        empty_df = pd.DataFrame()
        
        assert validate_consolidated_data(empty_df) is False
