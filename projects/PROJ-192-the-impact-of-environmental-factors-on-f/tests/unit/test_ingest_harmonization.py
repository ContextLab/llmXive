"""
Unit tests for environmental matrix harmonization (T013d).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pipelines.ingest import (
    _harmonize_column_names,
    _validate_required_columns,
    _clean_numeric_columns,
    _harmonize_biome_labels,
    _merge_duplicate_samples,
    validate_environmental_matrix
)

class TestHarmonizeColumnNames:
    def test_standard_columns(self):
        """Test that standard column names are preserved."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'pH': [6.5, 7.0],
            'biome': ['forest', 'grassland']
        })
        result = _harmonize_column_names(df)
        assert 'sample_id' in result.columns
        assert 'pH' in result.columns
        assert 'biome' in result.columns

    def test_case_insensitive(self):
        """Test that column name matching is case insensitive."""
        df = pd.DataFrame({
            'Sample_ID': ['s1', 's2'],
            'PH': [6.5, 7.0],
            'BIOME': ['forest', 'grassland']
        })
        result = _harmonize_column_names(df)
        assert 'sample_id' in result.columns
        assert 'pH' in result.columns
        assert 'biome' in result.columns

    def test_variations_mapped(self):
        """Test that common variations are mapped to standard names."""
        df = pd.DataFrame({
            'soil_ph': [6.5, 7.0],
            'nutrient': [10, 20],
            'habitat': ['forest', 'grassland'],
            'lat': [40.0, 41.0],
            'lon': [-70.0, -71.0]
        })
        result = _harmonize_column_names(df)
        assert 'pH' in result.columns
        assert 'nutrients' in result.columns
        assert 'biome' in result.columns
        assert 'latitude' in result.columns
        assert 'longitude' in result.columns

    def test_no_sample_id_creates_default(self):
        """Test that a sample_id column is created if missing."""
        df = pd.DataFrame({
            'pH': [6.5, 7.0]
        })
        result = _harmonize_column_names(df)
        assert 'sample_id' in result.columns
        assert len(result) == 2

class TestValidateRequiredColumns:
    def test_all_columns_present(self):
        """Test validation when all required columns are present."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'pH': [6.5, 7.0],
            'nutrients': [10, 20],
            'biome': ['forest', 'grassland'],
            'latitude': [40.0, 41.0],
            'longitude': [-70.0, -71.0]
        })
        result, missing = _validate_required_columns(df)
        assert len(missing) == 0
        assert len(result) == 2

    def test_missing_columns(self):
        """Test validation when some required columns are missing."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'pH': [6.5, 7.0]
        })
        result, missing = _validate_required_columns(df)
        assert 'nutrients' in missing
        assert 'biome' in missing
        # Only available columns should remain
        assert 'pH' in result.columns
        assert 'sample_id' in result.columns

    def test_drop_empty_sample_ids(self):
        """Test that rows with empty sample_ids are dropped."""
        df = pd.DataFrame({
            'sample_id': ['s1', '', None, 's4'],
            'pH': [6.5, 7.0, 7.5, 8.0]
        })
        result, _ = _validate_required_columns(df)
        assert len(result) == 2
        assert '' not in result['sample_id'].values
        assert pd.isna(result['sample_id']).sum() == 0

class TestCleanNumericColumns:
    def test_convert_strings_to_numeric(self):
        """Test conversion of string numbers to numeric."""
        df = pd.DataFrame({
            'pH': ['6.5', '7.0', 'invalid'],
            'latitude': ['40.0', '41.0', '42.0']
        })
        result = _clean_numeric_columns(df)
        assert result['pH'].dtype in [np.float64, np.float32]
        assert result['pH'].iloc[2] != result['pH'].iloc[2]  # NaN check
        assert result['latitude'].iloc[0] == 40.0

    def test_handles_missing_columns(self):
        """Test that missing columns don't cause errors."""
        df = pd.DataFrame({
            'pH': [6.5, 7.0]
        })
        result = _clean_numeric_columns(df)
        assert 'pH' in result.columns
        assert len(result) == 2

class TestHarmonizeBiomeLabels:
    def test_standardize_biome(self):
        """Test biome label standardization."""
        df = pd.DataFrame({
            'biome': ['temperate forest', 'TROPICAL FOREST', 'grassland', 'desert']
        })
        result = _harmonize_biome_labels(df)
        assert result['biome'].iloc[0] == 'Forest'
        assert result['biome'].iloc[1] == 'Forest'
        assert result['biome'].iloc[2] == 'Grassland'
        assert result['biome'].iloc[3] == 'Desert'

    def test_handles_missing_biome(self):
        """Test handling of missing biome column."""
        df = pd.DataFrame({
            'pH': [6.5, 7.0]
        })
        result = _harmonize_biome_labels(df)
        assert 'biome' not in result.columns

    def test_handles_unknown_biome(self):
        """Test that unknown biomes are capitalized."""
        df = pd.DataFrame({
            'biome': ['unknown_type', 'MARSH']
        })
        result = _harmonize_biome_labels(df)
        assert result['biome'].iloc[0] == 'Unknown_type' or result['biome'].iloc[0] == 'Unknown'
        assert result['biome'].iloc[1] == 'Marsh' or result['biome'].iloc[1] == 'Wetland'

class TestMergeDuplicateSamples:
    def test_remove_duplicates(self):
        """Test that duplicate sample_ids are removed."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's1', 's2', 's2', 's3'],
            'pH': [6.5, 7.0, 7.5, 8.0, 8.5]
        })
        result = _merge_duplicate_samples(df)
        assert len(result) == 3
        assert list(result['sample_id']) == ['s1', 's2', 's3']

    def test_no_duplicates(self):
        """Test that data without duplicates is unchanged."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2', 's3'],
            'pH': [6.5, 7.0, 7.5]
        })
        result = _merge_duplicate_samples(df)
        assert len(result) == 3

    def test_handles_missing_sample_id(self):
        """Test handling of missing sample_id column."""
        df = pd.DataFrame({
            'pH': [6.5, 7.0]
        })
        result = _merge_duplicate_samples(df)
        assert len(result) == 2

class TestValidateEnvironmentalMatrix:
    def test_valid_matrix(self, tmp_path):
        """Test validation of a valid matrix file."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'pH': [6.5, 7.0],
            'nutrients': [10, 20],
            'biome': ['forest', 'grassland'],
            'latitude': [40.0, 41.0],
            'longitude': [-70.0, -71.0]
        })
        file_path = tmp_path / "test_matrix.csv"
        df.to_csv(file_path, index=False)
        
        is_valid, msg = validate_environmental_matrix(str(file_path))
        assert is_valid
        assert "passed" in msg.lower()

    def test_missing_file(self, tmp_path):
        """Test validation when file doesn't exist."""
        is_valid, msg = validate_environmental_matrix(str(tmp_path / "nonexistent.csv"))
        assert not is_valid
        assert "not found" in msg.lower()

    def test_missing_columns(self, tmp_path):
        """Test validation with missing required columns."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'pH': [6.5, 7.0]
        })
        file_path = tmp_path / "incomplete.csv"
        df.to_csv(file_path, index=False)
        
        is_valid, msg = validate_environmental_matrix(str(file_path))
        assert not is_valid
        assert "missing" in msg.lower()

    def test_duplicates(self, tmp_path):
        """Test validation with duplicate sample_ids."""
        df = pd.DataFrame({
            'sample_id': ['s1', 's1', 's2'],
            'pH': [6.5, 7.0, 7.5],
            'nutrients': [10, 20, 30],
            'biome': ['forest', 'forest', 'grassland'],
            'latitude': [40.0, 41.0, 42.0],
            'longitude': [-70.0, -71.0, -72.0]
        })
        file_path = tmp_path / "duplicates.csv"
        df.to_csv(file_path, index=False)
        
        is_valid, msg = validate_environmental_matrix(str(file_path))
        assert not is_valid
        assert "duplicate" in msg.lower()

    def test_empty_file(self, tmp_path):
        """Test validation of empty file."""
        df = pd.DataFrame(columns=['sample_id', 'pH', 'nutrients', 'biome', 'latitude', 'longitude'])
        file_path = tmp_path / "empty.csv"
        df.to_csv(file_path, index=False)
        
        is_valid, msg = validate_environmental_matrix(str(file_path))
        assert not is_valid
        assert "empty" in msg.lower()