import os
import sys
import pytest
import pandas as pd
import tempfile
import shutil
from pathlib import Path

# Add code to path
sys.path.insert(0, 'code')

from process_data import split_geometry_disjoint, validate_splits, get_unique_geometries

class TestGeometryDisjointSplit:
    """Unit tests for geometry-disjoint split logic."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data with known geometry IDs."""
        # Create 20 rows with 5 unique geometry IDs (4 rows each)
        data = {
            'geometry_id': ['geo_A'] * 4 + ['geo_B'] * 4 + ['geo_C'] * 4 + ['geo_D'] * 4 + ['geo_E'] * 4,
            'translation': [[1.0, 2.0, 3.0]] * 20,
            'stability': [1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0],
            'initial_object_bounds': [[0.1, 0.2, 0.3]] * 20
        }
        return pd.DataFrame(data)

    def test_split_geometry_disjoint_creates_disjoint_sets(self, sample_data):
        """Test that train and test sets have no shared geometry IDs."""
        train_df, test_df = split_geometry_disjoint(sample_data, train_ratio=0.6, seed=42)
        
        train_geoms = set(train_df['geometry_id'].unique())
        test_geoms = set(test_df['geometry_id'].unique())
        
        assert train_geoms & test_geoms == set(), "Train and test sets share geometry IDs!"

    def test_split_preserves_all_geometries(self, sample_data):
        """Test that all original geometries are present in either train or test."""
        train_df, test_df = split_geometry_disjoint(sample_data, train_ratio=0.6, seed=42)
        
        original_geoms = set(sample_data['geometry_id'].unique())
        train_geoms = set(train_df['geometry_id'].unique())
        test_geoms = set(test_df['geometry_id'].unique())
        
        assert train_geoms | test_geoms == original_geoms, "Not all geometries preserved in split"

    def test_split_ratio_approximately_correct(self, sample_data):
        """Test that the split ratio is approximately correct."""
        train_df, test_df = split_geometry_disjoint(sample_data, train_ratio=0.8, seed=42)
        
        # With 5 geometries, 80% should be ~4 in train, 1 in test
        train_geom_count = len(set(train_df['geometry_id'].unique()))
        test_geom_count = len(set(test_df['geometry_id'].unique()))
        
        assert train_geom_count + test_geom_count == 5, "Total geometry count mismatch"
        assert train_geom_count == 4, f"Expected 4 train geometries, got {train_geom_count}"
        assert test_geom_count == 1, f"Expected 1 test geometry, got {test_geom_count}"

    def test_validate_splits_passes_correct_split(self, sample_data):
        """Test that validation passes for a correct split."""
        train_df, test_df = split_geometry_disjoint(sample_data, train_ratio=0.6, seed=42)
        assert validate_splits(train_df, test_df) is True

    def test_get_unique_geometries(self, sample_data):
        """Test extraction of unique geometry IDs."""
        unique_ids = get_unique_geometries(sample_data)
        assert len(unique_ids) == 5
        assert unique_ids == {'geo_A', 'geo_B', 'geo_C', 'geo_D', 'geo_E'}

    def test_reproducibility_with_seed(self, sample_data):
        """Test that same seed produces same split."""
        train_df1, test_df1 = split_geometry_disjoint(sample_data, train_ratio=0.6, seed=123)
        train_df2, test_df2 = split_geometry_disjoint(sample_data, train_ratio=0.6, seed=123)
        
        assert list(train_df1['geometry_id']) == list(train_df2['geometry_id'])
        assert list(test_df1['geometry_id']) == list(test_df2['geometry_id'])