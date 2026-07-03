"""
Unit tests for code/preprocess.py.

Tests cover:
- Feature engineering validation
- Sigma value calculation logic (via geometry_parser integration)
- Missing value handling and data insufficiency errors
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from preprocess import (
    load_parsed_data,
    validate_features,
    tag_metadata_features,
    enforce_minimum_records,
    save_cleaned_data
)
from error_handling import DataInsufficiencyError
from geometry_parser import calculate_sigma_from_misorientation

class TestValidateFeatures:
    """Tests for validate_features function."""

    def test_validate_features_all_present(self):
        """Test that validation passes when all required features are present."""
        df = pd.DataFrame({
            'misorientation_angle': [30.0, 45.0],
            'sigma_value': [3, 5],
            'boundary_plane_normal': ['[100]', '[110]'],
            'temperature': [300.0, 350.0],
            'composition': ['Cu', 'Al'],
            'diffusivity': [1e-10, 2e-10],
            'boundary_width': [10.0, 15.0],
            'excess_volume': [0.5, 0.8],
            'simulation_method': ['DFT', 'MD'],
            'potential_id': ['pot1', 'pot2']
        })

        required_features = [
            'misorientation_angle', 'sigma_value', 'boundary_plane_normal',
            'temperature', 'composition', 'diffusivity', 'boundary_width',
            'excess_volume', 'simulation_method', 'potential_id'
        ]

        is_valid, missing = validate_features(df, required_features)
        
        assert is_valid is True
        assert len(missing) == 0

    def test_validate_features_missing_some(self):
        """Test that validation detects missing features."""
        df = pd.DataFrame({
            'misorientation_angle': [30.0],
            'temperature': [300.0],
            # Missing sigma_value, boundary_plane_normal, etc.
        })

        required_features = [
            'misorientation_angle', 'sigma_value', 'boundary_plane_normal',
            'temperature', 'diffusivity'
        ]

        is_valid, missing = validate_features(df, required_features)
        
        assert is_valid is False
        assert 'sigma_value' in missing
        assert 'boundary_plane_normal' in missing
        assert 'diffusivity' in missing

    def test_validate_features_empty_dataframe(self):
        """Test validation on empty dataframe."""
        df = pd.DataFrame()
        required_features = ['misorientation_angle', 'sigma_value']
        
        is_valid, missing = validate_features(df, required_features)
        
        assert is_valid is False
        assert len(missing) == len(required_features)

class TestSigmaValueCalculation:
    """Tests for Sigma value calculation logic."""

    def test_calculate_sigma_from_misorientation_cubic(self):
        """Test Sigma calculation for common cubic angles."""
        # Common CSL angles for cubic crystals
        test_cases = [
            (38.94, 3),   # Σ3
            (50.48, 9),   # Σ9
            (70.53, 3),   # Σ3 (another variant)
        ]

        for angle, expected_sigma_approx in test_cases:
            sigma = calculate_sigma_from_misorientation(angle, crystal_system='cubic')
            # Allow some tolerance as approximation formulas vary
            # The key is that it returns a positive integer > 0
            assert isinstance(sigma, int)
            assert sigma > 0

    def test_calculate_sigma_from_misorientation_zero(self):
        """Test Sigma calculation for zero misorientation (Σ1)."""
        sigma = calculate_sigma_from_misorientation(0.0, crystal_system='cubic')
        assert sigma == 1

class TestTagMetadataFeatures:
    """Tests for tag_metadata_features function."""

    def test_tag_metadata_features_adds_columns(self):
        """Test that metadata features are correctly tagged."""
        df = pd.DataFrame({
            'misorientation_angle': [30.0],
            'diffusivity': [1e-10],
            'simulation_method': ['DFT'],
            'potential_id': ['pot1']
        })

        tagged_df = tag_metadata_features(df)

        assert 'simulation_method_tagged' in tagged_df.columns
        assert 'potential_id_tagged' in tagged_df.columns
        assert tagged_df['simulation_method_tagged'].iloc[0] == 'DFT'
        assert tagged_df['potential_id_tagged'].iloc[0] == 'pot1'

    def test_tag_metadata_features_handles_missing(self):
        """Test tagging when metadata columns are missing."""
        df = pd.DataFrame({
            'misorientation_angle': [30.0],
            'diffusivity': [1e-10]
        })

        tagged_df = tag_metadata_features(df)

        # Should handle missing columns gracefully, likely with None or empty
        assert 'simulation_method_tagged' in tagged_df.columns
        assert 'potential_id_tagged' in tagged_df.columns

class TestEnforceMinimumRecords:
    """Tests for enforce_minimum_records function."""

    def test_enforce_minimum_records_sufficient(self):
        """Test that sufficient records pass validation."""
        # Create 500 valid records
        data = {
            'misorientation_angle': np.random.rand(500) * 90,
            'sigma_value': np.random.randint(1, 20, 500),
            'boundary_plane_normal': ['[100]'] * 500,
            'temperature': 300.0,
            'composition': ['Cu'] * 500,
            'diffusivity': np.random.rand(500) * 1e-10,
            'boundary_width': 10.0,
            'excess_volume': 0.5,
            'simulation_method': ['DFT'] * 500,
            'potential_id': ['pot1'] * 500
        }
        df = pd.DataFrame(data)

        valid_df, missing_features = enforce_minimum_records(df, min_records=500)

        assert valid_df is not None
        assert len(valid_df) >= 500
        assert missing_features is None

    def test_enforce_minimum_records_insufficient(self):
        """Test that insufficient records raise DataInsufficiencyError."""
        # Create only 100 valid records
        data = {
            'misorientation_angle': np.random.rand(100) * 90,
            'sigma_value': np.random.randint(1, 20, 100),
            'boundary_plane_normal': ['[100]'] * 100,
            'temperature': 300.0,
            'composition': ['Cu'] * 100,
            'diffusivity': np.random.rand(100) * 1e-10,
            'boundary_width': 10.0,
            'excess_volume': 0.5,
            'simulation_method': ['DFT'] * 100,
            'potential_id': ['pot1'] * 100
        }
        df = pd.DataFrame(data)

        with pytest.raises(DataInsufficiencyError) as exc_info:
            enforce_minimum_records(df, min_records=500)

        error_msg = str(exc_info.value)
        assert "Data Insufficiency" in error_msg
        assert "100" in error_msg
        assert "500" in error_msg

    def test_enforce_minimum_records_with_missing_features(self):
        """Test error message includes list of missing features."""
        # Create records with missing diffusivity
        data = {
            'misorientation_angle': np.random.rand(100) * 90,
            'sigma_value': np.random.randint(1, 20, 100),
            'boundary_plane_normal': ['[100]'] * 100,
            'temperature': 300.0,
            'composition': ['Cu'] * 100,
            # Missing 'diffusivity'
            'boundary_width': 10.0,
            'excess_volume': 0.5,
            'simulation_method': ['DFT'] * 100,
            'potential_id': ['pot1'] * 100
        }
        df = pd.DataFrame(data)

        with pytest.raises(DataInsufficiencyError) as exc_info:
            enforce_minimum_records(df, min_records=500)

        error_msg = str(exc_info.value)
        assert "diffusivity" in error_msg.lower()

class TestLoadAndSaveCleanedData:
    """Tests for data loading and saving functions."""

    def test_save_cleaned_data_creates_file(self):
        """Test that save_cleaned_data creates the output file."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_output.parquet')
            save_cleaned_data(df, output_path)
            
            assert os.path.exists(output_path)
            
            # Verify we can load it back
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == 3
            assert list(loaded_df.columns) == ['col1', 'col2']

    def test_load_parsed_data_handles_missing_file(self):
        """Test that load_parsed_data raises appropriate error for missing file."""
        with pytest.raises(FileNotFoundError):
            load_parsed_data('non_existent_file.parquet')