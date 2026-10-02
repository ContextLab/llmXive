"""
Unit tests for merge_data.py module.

Tests focus on species-level stratification and uniqueness of species IDs
in the merged output to prevent GroupKFold leakage.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from merge_data import (
    load_rsa_metrics,
    load_physiological_data,
    merge_datasets,
    validate_sample_size
)

class TestMergeDatasets:
    """Tests for the merge_datasets function."""

    def test_merge_preserves_unique_species_ids(self, tmp_path):
        """
        Test that merged output has unique species IDs.
        
        This verifies the species-level stratification requirement.
        """
        # Create temporary CSV files
        rsa_data = pd.DataFrame({
            'species_id': ['Species_A', 'Species_B', 'Species_C'],
            'depth': [10.5, 12.3, 8.7],
            'branching_density': [0.5, 0.7, 0.3],
            'surface_area': [100.0, 150.0, 80.0]
        })
        
        physio_data = pd.DataFrame({
            'species_id': ['Species_A', 'Species_B', 'Species_C'],
            'conductance': [0.2, 0.3, 0.1],
            'photosynthesis': [5.0, 7.0, 3.0]
        })
        
        # Write to temp files
        rsa_path = tmp_path / "rsametrics.csv"
        physio_path = tmp_path / "physio_traits.csv"
        
        rsa_data.to_csv(rsa_path, index=False)
        physio_data.to_csv(physio_path, index=False)
        
        # Load and merge
        rsa_df = load_rsa_metrics(rsa_path)
        physio_df = load_physiological_data(physio_path)
        merged_df = merge_datasets(rsa_df, physio_df)
        
        # Assert unique species IDs
        assert merged_df['species_id'].is_unique, "Merged dataset should have unique species IDs"
        assert len(merged_df) == 3, "Should have 3 rows"
        
    def test_merge_handles_duplicates_by_dropping(self, tmp_path):
        """
        Test that duplicate species entries are dropped to ensure uniqueness.
        """
        # Create data with duplicates in one source
        rsa_data = pd.DataFrame({
            'species_id': ['Species_A', 'Species_A', 'Species_B', 'Species_C'],
            'depth': [10.5, 11.0, 12.3, 8.7],
            'branching_density': [0.5, 0.6, 0.7, 0.3],
            'surface_area': [100.0, 105.0, 150.0, 80.0]
        })
        
        physio_data = pd.DataFrame({
            'species_id': ['Species_A', 'Species_B', 'Species_C'],
            'conductance': [0.2, 0.3, 0.1],
            'photosynthesis': [5.0, 7.0, 3.0]
        })
        
        # Write to temp files
        rsa_path = tmp_path / "rsametrics.csv"
        physio_path = tmp_path / "physio_traits.csv"
        
        rsa_data.to_csv(rsa_path, index=False)
        physio_data.to_csv(physio_path, index=False)
        
        # Load and merge
        rsa_df = load_rsa_metrics(rsa_path)
        physio_df = load_physiological_data(physio_path)
        merged_df = merge_datasets(rsa_df, physio_df)
        
        # Assert unique species IDs after deduplication
        assert merged_df['species_id'].is_unique, "Merged dataset should have unique species IDs after dedup"
        assert len(merged_df) == 3, "Should have 3 rows after dropping duplicates"
        # Verify first occurrence is kept
        assert merged_df.loc[merged_df['species_id'] == 'Species_A', 'depth'].iloc[0] == 10.5
        
    def test_merge_inner_join_listwise_deletion(self, tmp_path):
        """
        Test that inner join correctly performs listwise deletion.
        """
        # Create data with non-overlapping species
        rsa_data = pd.DataFrame({
            'species_id': ['Species_A', 'Species_B', 'Species_C'],
            'depth': [10.5, 12.3, 8.7],
            'branching_density': [0.5, 0.7, 0.3],
            'surface_area': [100.0, 150.0, 80.0]
        })
        
        physio_data = pd.DataFrame({
            'species_id': ['Species_B', 'Species_C', 'Species_D'],  # Species_A and D don't overlap
            'conductance': [0.3, 0.1, 0.4],
            'photosynthesis': [7.0, 3.0, 8.0]
        })
        
        # Write to temp files
        rsa_path = tmp_path / "rsametrics.csv"
        physio_path = tmp_path / "physio_traits.csv"
        
        rsa_data.to_csv(rsa_path, index=False)
        physio_data.to_csv(physio_path, index=False)
        
        # Load and merge
        rsa_df = load_rsa_metrics(rsa_path)
        physio_df = load_physiological_data(physio_path)
        merged_df = merge_datasets(rsa_df, physio_df)
        
        # Assert only overlapping species are present
        assert len(merged_df) == 2, "Should have 2 rows (Species_B and Species_C)"
        assert 'Species_A' not in merged_df['species_id'].values
        assert 'Species_D' not in merged_df['species_id'].values
        assert 'Species_B' in merged_df['species_id'].values
        assert 'Species_C' in merged_df['species_id'].values

class TestValidateSampleSize:
    """Tests for the validate_sample_size function."""

    def test_validate_passes_sufficient_size(self):
        """Test validation passes when N >= 55."""
        df = pd.DataFrame({'species_id': [f'Species_{i}' for i in range(60)]})
        result = validate_sample_size(df, min_size=55)
        assert result is True

    def test_validate_fails_insufficient_size(self):
        """Test validation fails when N < 55."""
        df = pd.DataFrame({'species_id': [f'Species_{i}' for i in range(50)]})
        with pytest.raises(RuntimeError, match="Insufficient species after merge"):
            validate_sample_size(df, min_size=55)

    def test_validate_custom_min_size(self):
        """Test validation with custom minimum size."""
        df = pd.DataFrame({'species_id': [f'Species_{i}' for i in range(10)]})
        with pytest.raises(RuntimeError, match="Insufficient species after merge"):
            validate_sample_size(df, min_size=15)
        # Should pass with smaller min_size
        result = validate_sample_size(df, min_size=10)
        assert result is True
