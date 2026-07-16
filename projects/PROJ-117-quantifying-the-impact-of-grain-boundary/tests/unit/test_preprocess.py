"""
Unit tests for code/preprocess.py functionality.

Tests cover:
1. Feature engineering validation
2. Σ value extraction/calculation logic
3. Missing value handling and data insufficiency checks
4. Sampling application
5. Exclusion report generation
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocess import (
    load_parsed_data,
    validate_features,
    tag_metadata_features,
    apply_sampling,
    enforce_minimum_records,
    write_exclusion_report,
    save_cleaned_data
)
from error_handling import DataInsufficiencyError
from models.grain_boundary_record import GrainBoundaryRecord


class TestLoadParsedData:
    """Tests for load_parsed_data function."""

    def test_load_parquet_success(self, tmp_path):
        """Test successful loading of parquet file."""
        # Create test data
        test_df = pd.DataFrame({
            'misorientation_angle': [10.5, 20.3, 15.7],
            'sigma_value': [5, 3, 7],
            'diffusivity': [1e-10, 2e-10, 1.5e-10],
            'temperature': [800, 900, 850]
        })

        output_path = tmp_path / "test_parsed.parquet"
        test_df.to_parquet(output_path)

        # Load and verify
        loaded_df = load_parsed_data(str(output_path))

        assert loaded_df is not None
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == list(test_df.columns)
        assert loaded_df['misorientation_angle'].iloc[0] == 10.5

    def test_load_parquet_file_not_found(self):
        """Test handling of missing parquet file."""
        with pytest.raises(FileNotFoundError):
            load_parsed_data("nonexistent/file.parquet")

    def test_load_parquet_empty_file(self, tmp_path):
        """Test loading empty parquet file."""
        output_path = tmp_path / "empty.parquet"
        pd.DataFrame().to_parquet(output_path)

        loaded_df = load_parsed_data(str(output_path))
        assert loaded_df is not None
        assert len(loaded_df) == 0


class TestValidateFeatures:
    """Tests for validate_features function."""

    def test_all_features_present(self):
        """Test validation when all required features are present."""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0],
            'rodrigues_vector': [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            'boundary_plane_normal': [[1, 0, 0], [0, 1, 0]],
            'sigma_value': [5, 3],
            'boundary_width': [5.0, 6.0],
            'excess_volume': [0.1, 0.2],
            'temperature': [800, 900],
            'composition': ['CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10],
            'simulation_method': ['DFT', 'MD'],
            'potential_id': ['pot1', 'pot2']
        })

        required_features = [
            'misorientation_angle', 'rodrigues_vector', 'boundary_plane_normal',
            'sigma_value', 'boundary_width', 'excess_volume', 'temperature',
            'composition', 'diffusivity', 'simulation_method', 'potential_id'
        ]

        valid_df, missing_features = validate_features(df, required_features)

        assert len(missing_features) == 0
        assert len(valid_df) == 2

    def test_missing_required_features(self):
        """Test validation when some required features are missing."""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0],
            'temperature': [800, 900],
            'diffusivity': [1e-10, 2e-10]
        })

        required_features = [
            'misorientation_angle', 'rodrigues_vector', 'boundary_plane_normal',
            'sigma_value', 'boundary_width', 'excess_volume', 'temperature',
            'composition', 'diffusivity', 'simulation_method', 'potential_id'
        ]

        valid_df, missing_features = validate_features(df, required_features)

        assert len(missing_features) == 8  # All except misorientation_angle, temperature, diffusivity
        assert 'rodrigues_vector' in missing_features
        assert 'sigma_value' in missing_features
        assert len(valid_df) == 0

    def test_null_values_in_features(self):
        """Test validation with null values in required features."""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, np.nan, 20.0],
            'rodrigues_vector': [[0.1, 0.2, 0.3], None, [0.4, 0.5, 0.6]],
            'boundary_plane_normal': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            'sigma_value': [5, 3, np.nan],
            'boundary_width': [5.0, 6.0, 7.0],
            'excess_volume': [0.1, 0.2, 0.3],
            'temperature': [800, 900, 850],
            'composition': ['CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10, 1.5e-10],
            'simulation_method': ['DFT', 'MD', 'KMC'],
            'potential_id': ['pot1', 'pot2', 'pot3']
        })

        required_features = [
            'misorientation_angle', 'rodrigues_vector', 'boundary_plane_normal',
            'sigma_value', 'boundary_width', 'excess_volume', 'temperature',
            'composition', 'diffusivity', 'simulation_method', 'potential_id'
        ]

        valid_df, missing_features = validate_features(df, required_features)

        # Should filter out rows with null values
        assert len(valid_df) < len(df)
        assert valid_df['misorientation_angle'].isnull().sum() == 0


class TestTagMetadataFeatures:
    """Tests for tag_metadata_features function."""

    def test_tag_simulation_method(self):
        """Test tagging of simulation method."""
        df = pd.DataFrame({
            'simulation_method': ['DFT', 'MD', 'KMC', 'DFT'],
            'other_feature': [1, 2, 3, 4]
        })

        tagged_df = tag_metadata_features(df)

        # Check that simulation_method is present and tagged
        assert 'simulation_method' in tagged_df.columns
        assert set(tagged_df['simulation_method'].unique()) == {'DFT', 'MD', 'KMC'}

    def test_tag_potential_id(self):
        """Test tagging of potential ID."""
        df = pd.DataFrame({
            'potential_id': ['pot1', 'pot2', 'pot1'],
            'other_feature': [1, 2, 3]
        })

        tagged_df = tag_metadata_features(df)

        assert 'potential_id' in tagged_df.columns
        assert set(tagged_df['potential_id'].unique()) == {'pot1', 'pot2'}

    def test_missing_metadata_features(self):
        """Test handling when metadata features are missing."""
        df = pd.DataFrame({
            'other_feature': [1, 2, 3]
        })

        tagged_df = tag_metadata_features(df)

        # Should still work, just without the metadata columns
        assert 'other_feature' in tagged_df.columns


class TestApplySampling:
    """Tests for apply_sampling function."""

    def test_sampling_with_config(self, tmp_path):
        """Test sampling using sample_config.yaml."""
        # Create sample config
        config = {
            'sampling': {
                'enabled': True,
                'strategy': 'first_n',
                'n': 100
            }
        }

        config_path = tmp_path / "sample_config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        # Create large dataset
        df = pd.DataFrame({
            'feature': list(range(1000))
        })

        sampled_df = apply_sampling(df, str(config_path))

        assert len(sampled_df) == 100
        assert list(sampled_df['feature']) == list(range(100))

    def test_sampling_disabled(self, tmp_path):
        """Test when sampling is disabled."""
        config = {
            'sampling': {
                'enabled': False
            }
        }

        config_path = tmp_path / "sample_config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        df = pd.DataFrame({
            'feature': list(range(1000))
        })

        sampled_df = apply_sampling(df, str(config_path))

        assert len(sampled_df) == 1000

    def test_random_sampling(self, tmp_path):
        """Test random sampling strategy."""
        config = {
            'sampling': {
                'enabled': True,
                'strategy': 'random',
                'n': 50,
                'seed': 42
            }
        }

        config_path = tmp_path / "sample_config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        df = pd.DataFrame({
            'feature': list(range(1000))
        })

        sampled_df = apply_sampling(df, str(config_path))

        assert len(sampled_df) == 50
        # With fixed seed, should be reproducible
        sampled_df2 = apply_sampling(df, str(config_path))
        assert list(sampled_df['feature']) == list(sampled_df2['feature'])


class TestEnforceMinimumRecords:
    """Tests for enforce_minimum_records function."""

    def test_sufficient_records(self):
        """Test when record count meets minimum."""
        df = pd.DataFrame({
            'feature': list(range(500))
        })

        result_df = enforce_minimum_records(df, min_records=500)

        assert len(result_df) == 500

    def test_insufficient_records_raises_error(self):
        """Test that insufficient records raise DataInsufficiencyError."""
        df = pd.DataFrame({
            'feature': list(range(499))
        })

        with pytest.raises(DataInsufficiencyError):
            enforce_minimum_records(df, min_records=500)

    def test_insufficient_records_with_missing_features(self):
        """Test error message includes missing features."""
        df = pd.DataFrame({
            'feature': list(range(100))
        })

        # Create a mock to capture the error
        with pytest.raises(DataInsufficiencyError) as exc_info:
            enforce_minimum_records(df, min_records=500)

        error_msg = str(exc_info.value)
        assert "Data Insufficiency" in error_msg
        assert "100" in error_msg  # Retrieved count
        assert "500" in error_msg  # Required count


class TestWriteExclusionReport:
    """Tests for write_exclusion_report function."""

    def test_write_report_success(self, tmp_path):
        """Test successful writing of exclusion report."""
        report_path = tmp_path / "exclusion_report.json"

        excluded_records = 50
        missing_features = ['sigma_value', 'boundary_plane_normal']
        total_records = 1000

        write_exclusion_report(
            str(report_path),
            excluded_records,
            missing_features,
            total_records
        )

        assert report_path.exists()

        with open(report_path, 'r') as f:
            report = json.load(f)

        assert report['excluded_count'] == 50
        assert report['total_records'] == 1000
        assert set(report['missing_features']) == {'sigma_value', 'boundary_plane_normal'}

    def test_write_report_empty_missing_features(self, tmp_path):
        """Test writing report with no missing features."""
        report_path = tmp_path / "exclusion_report.json"

        write_exclusion_report(
            str(report_path),
            0,
            [],
            1000
        )

        with open(report_path, 'r') as f:
            report = json.load(f)

        assert report['excluded_count'] == 0
        assert report['missing_features'] == []

    def test_write_report_creates_directory(self, tmp_path):
        """Test that report creation handles missing directories."""
        report_path = tmp_path / "subdir" / "exclusion_report.json"

        write_exclusion_report(
            str(report_path),
            10,
            ['feature1'],
            100
        )

        assert report_path.exists()


class TestSaveCleanedData:
    """Tests for save_cleaned_data function."""

    def test_save_parquet_success(self, tmp_path):
        """Test successful saving of cleaned data."""
        df = pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': ['a', 'b', 'c']
        })

        output_path = tmp_path / "cleaned.parquet"

        save_cleaned_data(df, str(output_path))

        assert output_path.exists()

        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['feature1', 'feature2']

    def test_save_empty_dataframe(self, tmp_path):
        """Test saving empty dataframe."""
        df = pd.DataFrame()

        output_path = tmp_path / "empty_cleaned.parquet"

        save_cleaned_data(df, str(output_path))

        assert output_path.exists()
        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == 0


class TestSigmaValueHandling:
    """Specific tests for Σ value extraction and calculation logic."""

    def test_sigma_value_in_metadata(self):
        """Test handling when Σ value is present in metadata."""
        df = pd.DataFrame({
            'sigma_value': [5, 3, 7, np.nan],
            'other_feature': [1, 2, 3, 4]
        })

        required_features = ['sigma_value']
        valid_df, missing_features = validate_features(df, required_features)

        # Should filter out the row with NaN sigma_value
        assert len(valid_df) == 3
        assert all(valid_df['sigma_value'].notna())

    def test_sigma_value_calculation_logic(self):
        """Test that missing sigma values are properly identified."""
        df = pd.DataFrame({
            'sigma_value': [np.nan, np.nan, np.nan],
            'other_feature': [1, 2, 3]
        })

        required_features = ['sigma_value']
        valid_df, missing_features = validate_features(df, required_features)

        assert len(valid_df) == 0
        assert 'sigma_value' in missing_features

    def test_sigma_value_with_misorientation(self):
        """Test relationship between sigma and misorientation in validation."""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [5, np.nan, 3],
            'other_feature': [1, 2, 3]
        })

        required_features = ['misorientation_angle', 'sigma_value']
        valid_df, missing_features = validate_features(df, required_features)

        # Should keep only rows with both features valid
        assert len(valid_df) == 2
        assert valid_df['sigma_value'].isnull().sum() == 0


class TestMissingValueHandling:
    """Comprehensive tests for missing value handling."""

    def test_multiple_missing_features(self):
        """Test handling when multiple features have missing values."""
        df = pd.DataFrame({
            'feature1': [1, np.nan, 3, 4],
            'feature2': [np.nan, 2, 3, 4],
            'feature3': [1, 2, np.nan, 4]
        })

        required_features = ['feature1', 'feature2', 'feature3']
        valid_df, missing_features = validate_features(df, required_features)

        # Should only keep rows with all features present
        assert len(valid_df) == 1
        assert valid_df.iloc[0]['feature1'] == 4
        assert valid_df.iloc[0]['feature2'] == 4
        assert valid_df.iloc[0]['feature3'] == 4

    def test_all_values_missing(self):
        """Test when all values in a required feature are missing."""
        df = pd.DataFrame({
            'feature1': [np.nan, np.nan, np.nan],
            'feature2': [1, 2, 3]
        })

        required_features = ['feature1', 'feature2']
        valid_df, missing_features = validate_features(df, required_features)

        assert len(valid_df) == 0
        assert 'feature1' in missing_features

    def test_string_features_with_nulls(self):
        """Test handling of string features with null values."""
        df = pd.DataFrame({
            'simulation_method': ['DFT', None, 'MD'],
            'potential_id': ['pot1', 'pot2', None],
            'feature': [1, 2, 3]
        })

        required_features = ['simulation_method', 'potential_id']
        valid_df, missing_features = validate_features(df, required_features)

        # Should filter out rows with any null in required string features
        assert len(valid_df) == 0


class TestIntegrationScenarios:
    """Integration-style tests for common preprocessing scenarios."""

    def test_full_preprocessing_pipeline(self, tmp_path):
        """Test end-to-end preprocessing with all components."""
        # Create sample data
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0, 40.0, 50.0],
            'rodrigues_vector': [[0.1, 0.2, 0.3]] * 5,
            'boundary_plane_normal': [[1, 0, 0]] * 5,
            'sigma_value': [5, 3, 7, 5, 3],
            'boundary_width': [5.0, 6.0, 7.0, 8.0, 9.0],
            'excess_volume': [0.1, 0.2, 0.3, 0.4, 0.5],
            'temperature': [800, 900, 850, 900, 800],
            'composition': ['CeO2'] * 5,
            'diffusivity': [1e-10, 2e-10, 1.5e-10, 1.8e-10, 1.2e-10],
            'simulation_method': ['DFT', 'MD', 'KMC', 'DFT', 'MD'],
            'potential_id': ['pot1', 'pot2', 'pot3', 'pot1', 'pot2']
        })

        # Save to temp file
        input_path = tmp_path / "parsed.parquet"
        df.to_parquet(input_path)

        # Load and validate
        loaded_df = load_parsed_data(str(input_path))
        required_features = [
            'misorientation_angle', 'rodrigues_vector', 'boundary_plane_normal',
            'sigma_value', 'boundary_width', 'excess_volume', 'temperature',
            'composition', 'diffusivity', 'simulation_method', 'potential_id'
        ]
        valid_df, missing_features = validate_features(loaded_df, required_features)

        # Tag metadata
        tagged_df = tag_metadata_features(valid_df)

        # Apply sampling (disable for this test)
        config_path = tmp_path / "sample_config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump({'sampling': {'enabled': False}}, f)

        sampled_df = apply_sampling(tagged_df, str(config_path))

        # Enforce minimum (should pass with 5 records if min is 5)
        final_df = enforce_minimum_records(sampled_df, min_records=5)

        # Write exclusion report
        report_path = tmp_path / "exclusion_report.json"
        write_exclusion_report(str(report_path), 0, [], len(df))

        # Save cleaned data
        output_path = tmp_path / "cleaned.parquet"
        save_cleaned_data(final_df, str(output_path))

        # Verify outputs
        assert output_path.exists()
        assert report_path.exists()

        final_loaded = pd.read_parquet(output_path)
        assert len(final_loaded) == 5

    def test_data_insufficiency_scenario(self, tmp_path):
        """Test scenario where data is insufficient."""
        # Create small dataset
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0],
            'rodrigues_vector': [[0.1, 0.2, 0.3]] * 2,
            'boundary_plane_normal': [[1, 0, 0]] * 2,
            'sigma_value': [5, 3],
            'boundary_width': [5.0, 6.0],
            'excess_volume': [0.1, 0.2],
            'temperature': [800, 900],
            'composition': ['CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10],
            'simulation_method': ['DFT', 'MD'],
            'potential_id': ['pot1', 'pot2']
        })

        with pytest.raises(DataInsufficiencyError):
            enforce_minimum_records(df, min_records=500)

    def test_exclusion_report_with_missing_features(self, tmp_path):
        """Test exclusion report generation when features are missing."""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, np.nan, 30.0],
            'rodrigues_vector': [[0.1, 0.2, 0.3], None, [0.4, 0.5, 0.6]],
            'boundary_plane_normal': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            'sigma_value': [5, 3, np.nan],
            'boundary_width': [5.0, 6.0, 7.0],
            'excess_volume': [0.1, 0.2, 0.3],
            'temperature': [800, 900, 850],
            'composition': ['CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10, 1.5e-10],
            'simulation_method': ['DFT', 'MD', 'KMC'],
            'potential_id': ['pot1', 'pot2', 'pot3']
        })

        required_features = [
            'misorientation_angle', 'rodrigues_vector', 'boundary_plane_normal',
            'sigma_value', 'boundary_width', 'excess_volume', 'temperature',
            'composition', 'diffusivity', 'simulation_method', 'potential_id'
        ]

        valid_df, missing_features = validate_features(df, required_features)

        report_path = tmp_path / "exclusion_report.json"
        write_exclusion_report(
            str(report_path),
            len(df) - len(valid_df),
            missing_features,
            len(df)
        )

        with open(report_path, 'r') as f:
            report = json.load(f)

        assert report['excluded_count'] == 2
        assert len(report['missing_features']) > 0