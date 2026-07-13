"""
Unit tests for Magpie descriptor generation (T012).

Tests verify that:
1. Magpie features are generated correctly for known compositions
2. No structural features are included (composition-only)
3. Invalid compositions are handled gracefully
4. Output schema matches expectations
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the module under test
from generate_descriptors import (
    compute_magpie_descriptors,
    validate_dataframe,
    load_raw_materials
)
from matminer.featurizers.composition import MagpieData

class TestMagpieDescriptorGeneration:
    """Tests for Magpie descriptor generation logic."""

    @pytest.fixture
    def sample_data(self):
        """Create sample material data for testing."""
        data = {
            'composition': ['Fe2O3', 'SiO2', 'NaCl', 'H2O', 'C6H12O6'],
            'property_name': ['melting_point', 'melting_point', 'melting_point', 
                             'melting_point', 'melting_point'],
            'property_value': [1565, 1713, 801, 100, 146]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def magpie_featurizer(self):
        """Return a MagpieData featurizer instance."""
        return MagpieData()

    def test_computes_magpie_features(self, sample_data):
        """Test that Magpie features are computed correctly."""
        result = compute_magpie_descriptors(sample_data, sample_size=5)
        
        # Check that features were added
        assert len(result) == 5
        assert 'property_name' in result.columns
        
        # Check that Magpie features exist (they should start with specific patterns)
        magpie_features = ['number', 'mean', 'std', 'minimum', 'maximum']
        found_features = any(
            any(col.startswith(f) for f in magpie_features) 
            for col in result.columns
        )
        assert found_features, "Magpie features not found in output"

    def test_composition_only_no_structure(self, sample_data, magpie_featurizer):
        """Verify that only composition features are generated (no structural data)."""
        result = compute_magpie_descriptors(sample_data, sample_size=5)
        
        # Get expected Magpie feature names
        expected_features = magpie_featurizer.feature_labels()
        
        # All expected features should be present
        for feature in expected_features:
            assert feature in result.columns, f"Missing feature: {feature}"
        
        # Verify no structural features (like 'structure_features' or similar)
        structural_keywords = ['structure', 'lattice', 'space_group', 'crystal']
        structural_cols = [
            col for col in result.columns 
            if any(kw in col.lower() for kw in structural_keywords)
        ]
        assert len(structural_cols) == 0, f"Found structural features: {structural_cols}"

    def test_invalid_composition_handling(self):
        """Test that invalid compositions are handled gracefully."""
        data = {
            'composition': ['Fe2O3', 'InvalidFormula', 'SiO2', ''],
            'property_name': ['mp', 'mp', 'mp', 'mp'],
            'property_value': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        # Should not raise an exception, but skip invalid entries
        result = compute_magpie_descriptors(df, sample_size=4)
        
        # Should have fewer rows than input (invalid ones skipped)
        assert len(result) < len(df)
        # Should be at least the valid ones
        assert len(result) >= 2

    def test_output_schema(self, sample_data):
        """Test that output matches expected schema."""
        result = compute_magpie_descriptors(sample_data, sample_size=5)
        
        # Required columns from input
        required_input_cols = ['composition', 'property_name', 'property_value']
        for col in required_input_cols:
            assert col in result.columns, f"Missing input column: {col}"
        
        # Magpie feature columns should be numeric
        magpie = MagpieData()
        expected_features = magpie.feature_labels()
        
        for feature in expected_features:
            assert feature in result.columns
            assert pd.api.types.is_numeric_dtype(result[feature])

    def test_deterministic_output(self, sample_data):
        """Test that output is deterministic with same seed."""
        result1 = compute_magpie_descriptors(sample_data, sample_size=5)
        result2 = compute_magpie_descriptors(sample_data, sample_size=5)
        
        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        data = {
            'composition': [],
            'property_name': [],
            'property_value': []
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="No data was successfully featurized"):
            compute_magpie_descriptors(df)

    def test_validate_dataframe_success(self, sample_data):
        """Test successful validation."""
        result = validate_dataframe(sample_data)
        assert result is not None
        assert len(result) == 5

    def test_validate_dataframe_missing_columns(self):
        """Test validation failure with missing columns."""
        data = {
            'composition': ['Fe2O3'],
            'wrong_col': [1]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_dataframe(df)

    def test_validate_dataframe_nan_composition(self):
        """Test validation with NaN compositions."""
        data = {
            'composition': ['Fe2O3', None, 'SiO2'],
            'property_name': ['mp', 'mp', 'mp'],
            'property_value': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        
        # Should drop NaN and return valid rows
        result = validate_dataframe(df)
        assert len(result) == 2
        assert result['composition'].isna().sum() == 0

class TestLoadRawMaterials:
    """Tests for raw data loading functionality."""

    def test_load_from_parquet(self, tmp_path):
        """Test loading data from parquet files."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create sample parquet file
        data = {
            'composition': ['Fe2O3', 'SiO2'],
            'property_name': ['mp', 'mp'],
            'property_value': [1, 2]
        }
        df = pd.DataFrame(data)
        parquet_file = raw_dir / "test.parquet"
        df.to_parquet(parquet_file)
        
        # Load and verify
        loaded_df = load_raw_materials(tmp_path)
        assert len(loaded_df) == 2
        assert 'composition' in loaded_df.columns

    def test_load_from_csv(self, tmp_path):
        """Test loading data from CSV files."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create sample CSV file
        data = {
            'composition': ['Fe2O3', 'SiO2'],
            'property_name': ['mp', 'mp'],
            'property_value': [1, 2]
        }
        df = pd.DataFrame(data)
        csv_file = raw_dir / "test.csv"
        df.to_csv(csv_file, index=False)
        
        # Load and verify
        loaded_df = load_raw_materials(tmp_path)
        assert len(loaded_df) == 2

    def test_load_from_json(self, tmp_path):
        """Test loading data from JSON files."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create sample JSON file
        data = [
            {'composition': 'Fe2O3', 'property_name': 'mp', 'property_value': 1},
            {'composition': 'SiO2', 'property_name': 'mp', 'property_value': 2}
        ]
        import json
        json_file = raw_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        # Load and verify
        loaded_df = load_raw_materials(tmp_path)
        assert len(loaded_df) == 2

    def test_no_files_found(self, tmp_path):
        """Test error when no data files are found."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        with pytest.raises(FileNotFoundError, match="No supported data files found"):
            load_raw_materials(tmp_path)

    def test_no_data_loaded(self, tmp_path):
        """Test error when files exist but contain no data."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create empty parquet file
        empty_df = pd.DataFrame()
        parquet_file = raw_dir / "empty.parquet"
        empty_df.to_parquet(parquet_file)
        
        with pytest.raises(ValueError, match="No data loaded"):
            load_raw_materials(tmp_path)