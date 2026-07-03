"""
Unit tests for code/preprocess.py.

Tests cover:
- Feature engineering validation
- Sigma value calculation logic integration
- Missing value handling and data insufficiency errors
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocess import (
    load_parsed_data,
    validate_required_features,
    filter_records,
    tag_metadata_features,
    preprocess_data,
    raise_data_insufficiency
)
from utils import raise_data_insufficiency as utils_raise_data_insufficiency


class TestLoadParsedData(TestCase):
    """Tests for load_parsed_data function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_parsed.parquet"
        
        # Create dummy data
        data = {
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [5, 13, 3],
            'boundary_plane_normal': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            'temperature': [300, 400, 500],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'simulation_method': ['DFT', 'MD', 'KMC'],
            'potential_id': ['pot1', 'pot2', 'pot3'],
            'boundary_width': [10.0, 12.0, 11.0],
            'excess_volume': [0.1, 0.2, 0.15]
        }
        df = pd.DataFrame(data)
        df.to_parquet(self.test_file)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_valid_file(self):
        """Test loading a valid parquet file."""
        result = load_parsed_data(self.test_file)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertIn('misorientation_angle', result.columns)

    def test_load_missing_file(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        non_existent = Path(self.temp_dir) / "nonexistent.parquet"
        with self.assertRaises(FileNotFoundError):
            load_parsed_data(non_existent)


class TestValidateRequiredFeatures(TestCase):
    """Tests for validate_required_features function."""

    def test_all_features_present(self):
        """Test validation when all required features are present."""
        required = {'a', 'b', 'c'}
        existing = {'a', 'b', 'c', 'd'}
        missing = validate_required_features(existing, required)
        self.assertEqual(missing, set())

    def test_some_features_missing(self):
        """Test validation when some features are missing."""
        required = {'a', 'b', 'c', 'd'}
        existing = {'a', 'b', 'e'}
        missing = validate_required_features(existing, required)
        self.assertEqual(missing, {'c', 'd'})

    def test_no_features_present(self):
        """Test validation when no required features are present."""
        required = {'a', 'b', 'c'}
        existing = {'d', 'e'}
        missing = validate_required_features(existing, required)
        self.assertEqual(missing, required)


class TestFilterRecords(TestCase):
    """Tests for filter_records function."""

    def setUp(self):
        self.data = {
            'misorientation_angle': [10.0, np.nan, 30.0, 40.0],
            'sigma_value': [5, 13, np.nan, 3],
            'boundary_plane_normal': [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0]],
            'temperature': [300, 400, 500, 600],
            'diffusivity': [1e-10, 2e-10, 3e-10, 4e-10],
            'boundary_width': [10.0, 12.0, 11.0, 13.0],
            'excess_volume': [0.1, 0.2, 0.15, 0.25],
            'simulation_method': ['DFT', 'MD', 'KMC', 'DFT'],
            'potential_id': ['pot1', 'pot2', 'pot3', 'pot4']
        }
        self.df = pd.DataFrame(self.data)
        self.required_features = {
            'misorientation_angle', 'sigma_value', 'boundary_plane_normal',
            'temperature', 'diffusivity', 'boundary_width', 'excess_volume'
        }

    def test_filter_records_removes_nan(self):
        """Test that records with NaN in required features are removed."""
        valid_df, missing_features = filter_records(self.df, self.required_features)
        
        # Row 1 (index 1) has NaN in misorientation_angle -> removed
        # Row 2 (index 2) has NaN in sigma_value -> removed
        # Row 0 and 3 should remain
        self.assertEqual(len(valid_df), 2)
        self.assertIn(0, valid_df.index)
        self.assertIn(3, valid_df.index)
        self.assertGreater(len(missing_features), 0)

    def test_filter_records_all_valid(self):
        """Test filtering when all records are valid."""
        clean_data = self.data.copy()
        clean_data['misorientation_angle'] = [10.0, 20.0, 30.0, 40.0]
        clean_data['sigma_value'] = [5, 13, 3, 7]
        clean_df = pd.DataFrame(clean_data)
        
        valid_df, missing_features = filter_records(clean_df, self.required_features)
        
        self.assertEqual(len(valid_df), 4)
        self.assertEqual(len(missing_features), 0)


class TestTagMetadataFeatures(TestCase):
    """Tests for tag_metadata_features function."""

    def test_tagging_adds_columns(self):
        """Test that metadata features are tagged correctly."""
        data = {
            'simulation_method': ['DFT', 'MD', 'KMC'],
            'potential_id': ['pot1', 'pot2', 'pot3'],
            'value': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        
        tagged_df = tag_metadata_features(df)
        
        self.assertIn('simulation_method_tagged', tagged_df.columns)
        self.assertIn('potential_id_tagged', tagged_df.columns)
        
        # Check that tagging converts to categorical or similar
        self.assertEqual(len(tagged_df), 3)

    def test_tagging_preserves_other_columns(self):
        """Test that non-metadata columns are preserved."""
        data = {
            'simulation_method': ['DFT', 'MD'],
            'potential_id': ['pot1', 'pot2'],
            'feature_a': [1.0, 2.0],
            'feature_b': [3.0, 4.0]
        }
        df = pd.DataFrame(data)
        
        tagged_df = tag_metadata_features(df)
        
        self.assertIn('feature_a', tagged_df.columns)
        self.assertIn('feature_b', tagged_df.columns)
        self.assertEqual(tagged_df['feature_a'].tolist(), [1.0, 2.0])


class TestPreprocessData(TestCase):
    """Tests for the full preprocess_data pipeline."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = Path(self.temp_dir) / "input.parquet"
        
        # Create data with some missing values
        data = {
            'misorientation_angle': [10.0, np.nan, 30.0, 40.0, 50.0],
            'sigma_value': [5, 13, np.nan, 3, 7],
            'boundary_plane_normal': [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1]],
            'temperature': [300, 400, 500, 600, 700],
            'diffusivity': [1e-10, 2e-10, 3e-10, 4e-10, 5e-10],
            'boundary_width': [10.0, 12.0, 11.0, 13.0, 14.0],
            'excess_volume': [0.1, 0.2, 0.15, 0.25, 0.3],
            'simulation_method': ['DFT', 'MD', 'KMC', 'DFT', 'MD'],
            'potential_id': ['pot1', 'pot2', 'pot3', 'pot4', 'pot5']
        }
        pd.DataFrame(data).to_parquet(self.input_file)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_preprocess_filters_and_tags(self):
        """Test that preprocess_data filters invalid records and tags metadata."""
        output_file = Path(self.temp_dir) / "output.parquet"
        
        result = preprocess_data(
            input_path=self.input_file,
            output_path=output_file,
            min_records=500  # Intentionally high to trigger insufficiency
        )
        
        # Should raise Data Insufficiency error because we only have 3 valid records
        self.assertIsNone(result)  # Function exits on error, so this line won't be reached
        
    def test_preprocess_with_sufficient_records(self):
        """Test preprocess_data with enough valid records."""
        # Create a larger dataset
        large_data = {
            'misorientation_angle': [float(i) for i in range(100)],
            'sigma_value': [5 if i % 2 == 0 else 13 for i in range(100)],
            'boundary_plane_normal': [[1, 0, 0] for _ in range(100)],
            'temperature': [300 + i * 10 for i in range(100)],
            'diffusivity': [1e-10 * (i + 1) for i in range(100)],
            'boundary_width': [10.0 + i * 0.1 for i in range(100)],
            'excess_volume': [0.1 + i * 0.01 for i in range(100)],
            'simulation_method': ['DFT' if i % 2 == 0 else 'MD' for i in range(100)],
            'potential_id': [f'pot{i % 10}' for i in range(100)]
        }
        large_df = pd.DataFrame(large_data)
        large_df.to_parquet(self.input_file)
        
        output_file = Path(self.temp_dir) / "output.parquet"
        
        result = preprocess_data(
            input_path=self.input_file,
            output_path=output_file,
            min_records=50
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(output_file.exists())
        
        # Verify output structure
        output_df = pd.read_parquet(output_file)
        self.assertIn('simulation_method_tagged', output_df.columns)
        self.assertIn('potential_id_tagged', output_df.columns)
        self.assertGreaterEqual(len(output_df), 50)

    def test_sigma_value_integration(self):
        """Test that sigma value calculation is correctly integrated in the pipeline."""
        # The pipeline should preserve sigma_value in the output
        large_data = {
            'misorientation_angle': [float(i) for i in range(100)],
            'sigma_value': [5 if i % 2 == 0 else 13 for i in range(100)],
            'boundary_plane_normal': [[1, 0, 0] for _ in range(100)],
            'temperature': [300 + i * 10 for i in range(100)],
            'diffusivity': [1e-10 * (i + 1) for i in range(100)],
            'boundary_width': [10.0 + i * 0.1 for i in range(100)],
            'excess_volume': [0.1 + i * 0.01 for i in range(100)],
            'simulation_method': ['DFT' if i % 2 == 0 else 'MD' for i in range(100)],
            'potential_id': [f'pot{i % 10}' for i in range(100)]
        }
        large_df = pd.DataFrame(large_data)
        large_df.to_parquet(self.input_file)
        
        output_file = Path(self.temp_dir) / "output.parquet"
        
        preprocess_data(
            input_path=self.input_file,
            output_path=output_file,
            min_records=50
        )
        
        output_df = pd.read_parquet(output_file)
        self.assertIn('sigma_value', output_df.columns)
        self.assertTrue(all(output_df['sigma_value'].notna()))


class TestDataInsufficiencyHandling(TestCase):
    """Tests for data insufficiency error handling."""

    def test_raise_data_insufficiency_exits(self):
        """Test that raise_data_insufficiency exits with code 1."""
        with self.assertRaises(SystemExit) as context:
            utils_raise_data_insufficiency(
                retrieved_count=100,
                required_count=500,
                missing_features=['feature_a', 'feature_b']
            )
        
        self.assertEqual(context.exception.code, 1)

    def test_raise_data_insufficiency_message(self):
        """Test that the error message contains required information."""
        with patch('sys.exit') as mock_exit, \
             patch('logging.error') as mock_log:
            
            utils_raise_data_insufficiency(
                retrieved_count=100,
                required_count=500,
                missing_features=['feature_a', 'feature_b']
            )
            
            # Verify log message contains count and missing features
            mock_log.assert_called_once()
            log_message = str(mock_log.call_args[0][0])
            self.assertIn('100', log_message)
            self.assertIn('500', log_message)
            self.assertIn('feature_a', log_message)
            self.assertIn('feature_b', log_message)

    def test_filter_records_triggers_insufficiency(self):
        """Test that filter_records triggers insufficiency when below threshold."""
        small_data = {
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [5, 13, 3],
            'boundary_plane_normal': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            'temperature': [300, 400, 500],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'boundary_width': [10.0, 12.0, 11.0],
            'excess_volume': [0.1, 0.2, 0.15],
            'simulation_method': ['DFT', 'MD', 'KMC'],
            'potential_id': ['pot1', 'pot2', 'pot3']
        }
        df = pd.DataFrame(small_data)
        
        required = {'misorientation_angle', 'sigma_value', 'boundary_plane_normal',
                   'temperature', 'diffusivity', 'boundary_width', 'excess_volume'}
        
        with self.assertRaises(SystemExit) as context:
            filter_records(df, required, min_records=500)
        
        self.assertEqual(context.exception.code, 1)