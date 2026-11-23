"""
Unit tests for data_ingestion.py functions.
Tests data filtering logic with mock API responses.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_ingestion import filter_and_impute, merge_datasets


class TestFilterAndImpute:
    """Tests for filter_and_impute function."""

    def test_filter_m_dwarfs(self):
        """Test that non-M-dwarfs are filtered out."""
        # Create mock data with spectral types
        mock_df = pd.DataFrame({
            'star_id': [1, 2, 3, 4, 5],
            'spectral_type': ['M0', 'K0', 'M5', 'G2', 'M3'],
            'flare_count': [15, 5, 20, 8, 12],
            'mass': [0.5, 0.8, 0.4, 1.0, 0.3],
            'radius': [0.5, 0.8, 0.4, 1.0, 0.3],
            'semi_major_axis': [0.1, 0.2, 0.15, 0.3, 0.12],
            'system_age': [5.0, 3.0, 6.0, 4.0, np.nan]
        })
        
        # Apply filtering
        filtered_df = filter_and_impute(mock_df)
        
        # Check that only M-dwarfs remain
        assert all(filtered_df['spectral_type'].str.startswith('M')), \
            "Only M-dwarf spectral types should remain"
        
        # Check that systems with <10 flares are removed
        assert all(filtered_df['flare_count'] >= 10), \
            "All remaining systems should have >= 10 flares"
        
        # Check that missing mass/radius are removed
        assert not filtered_df['mass'].isna().any(), "No missing mass values"
        assert not filtered_df['radius'].isna().any(), "No missing radius values"
        
        # Check that missing age is imputed
        assert not filtered_df['system_age'].isna().any(), \
            "Missing age values should be imputed"

    def test_filter_missing_required_columns(self):
        """Test filtering when required columns are missing."""
        mock_df = pd.DataFrame({
            'star_id': [1, 2, 3],
            'spectral_type': ['M0', 'M5', 'M3'],
            'flare_count': [15, 20, 12],
            # Missing mass, radius, semi_major_axis
        })
        
        # Should filter out all rows due to missing required columns
        filtered_df = filter_and_impute(mock_df)
        
        assert len(filtered_df) == 0, \
            "All rows should be filtered out due to missing required columns"

    def test_impute_age_with_default(self):
        """Test that missing age is imputed with default value."""
        from config import DEFAULT_M_DWARF_AGE
        
        mock_df = pd.DataFrame({
            'star_id': [1, 2],
            'spectral_type': ['M0', 'M5'],
            'flare_count': [15, 20],
            'mass': [0.5, 0.4],
            'radius': [0.5, 0.4],
            'semi_major_axis': [0.1, 0.15],
            'system_age': [np.nan, 6.0]
        })
        
        filtered_df = filter_and_impute(mock_df)
        
        # Check that missing age was imputed
        assert filtered_df.loc[filtered_df['star_id'] == 1, 'system_age'].iloc[0] == DEFAULT_M_DWARF_AGE, \
            f"Missing age should be imputed with {DEFAULT_M_DWARF_AGE}"


class TestMergeDatasets:
    """Tests for merge_datasets function."""

    def test_merge_datasets_success(self):
        """Test successful merge of flare and exoplanet data."""
        flare_df = pd.DataFrame({
            'host_star_id': [1, 2, 3, 4],
            'flare_count': [15, 20, 5, 12]
        })
        
        exoplanet_df = pd.DataFrame({
            'host_star_id': [1, 2, 3, 5],
            'mass': [0.5, 0.4, 0.6, 0.3],
            'radius': [0.5, 0.4, 0.6, 0.3],
            'semi_major_axis': [0.1, 0.15, 0.12, 0.2]
        })
        
        merged_df = merge_datasets(flare_df, exoplanet_df)
        
        # Check that merge was successful
        assert 'flare_count' in merged_df.columns, "Flare count should be in merged data"
        assert 'mass' in merged_df.columns, "Mass should be in merged data"
        assert 'radius' in merged_df.columns, "Radius should be in merged data"
        assert 'semi_major_axis' in merged_df.columns, "Semi-major axis should be in merged data"
        
        # Check that only matching records remain (inner join)
        assert len(merged_df) == 3, "Should have 3 matching records"
        
        # Check specific values
        assert merged_df.loc[merged_df['host_star_id'] == 1, 'flare_count'].iloc[0] == 15
        assert merged_df.loc[merged_df['host_star_id'] == 1, 'mass'].iloc[0] == 0.5

    def test_merge_datasets_no_matches(self):
        """Test merge when there are no matching star IDs."""
        flare_df = pd.DataFrame({
            'host_star_id': [1, 2, 3],
            'flare_count': [15, 20, 5]
        })
        
        exoplanet_df = pd.DataFrame({
            'host_star_id': [4, 5, 6],
            'mass': [0.5, 0.4, 0.6],
            'radius': [0.5, 0.4, 0.6],
            'semi_major_axis': [0.1, 0.15, 0.12]
        })
        
        merged_df = merge_datasets(flare_df, exoplanet_df)
        
        # Should return empty DataFrame
        assert len(merged_df) == 0, "Should return empty DataFrame when no matches"
