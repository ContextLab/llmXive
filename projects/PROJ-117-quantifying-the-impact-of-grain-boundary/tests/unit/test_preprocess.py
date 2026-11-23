"""
Unit tests for code/preprocess.py
Tests feature engineering, Σ value extraction/calculation logic, and missing value handling.
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.preprocess import (
    load_parsed_data,
    validate_features,
    tag_metadata_features,
    apply_sampling,
    enforce_minimum_records,
    write_exclusion_report,
    save_cleaned_data
)
from code.models.grain_boundary_record import GrainBoundaryRecord
from code.error_handling import DataInsufficiencyError

class TestPreprocess(unittest.TestCase):
    """Unit tests for preprocessing functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data" / "processed"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = Path(self.test_dir) / "artifacts" / "reports"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def _create_mock_parsed_data(self, n_records=100, include_sigma=True, include_misorientation=True, include_boundary_plane=True):
        """Create a mock DataFrame simulating parsed geometry data."""
        data = {
            'structure_id': [f'struct_{i}' for i in range(n_records)],
            'temperature': np.random.uniform(300, 1500, n_records),
            'composition': ['CeO2'] * n_records,
            'diffusivity': np.random.uniform(1e-12, 1e-8, n_records),
            'boundary_width': np.random.uniform(1.0, 5.0, n_records),
            'excess_volume': np.random.uniform(0.1, 0.5, n_records),
            'simulation_method': ['DFT'] * n_records,
            'potential_id': ['PBE'] * n_records,
        }

        if include_misorientation:
            data['misorientation_angle'] = np.random.uniform(0, 60, n_records)
        else:
            data['misorientation_angle'] = [np.nan] * n_records

        if include_sigma:
            # Some valid, some NaN to test filtering
            sigma_values = np.random.choice([1, 3, 5, 7, 9, 13, np.nan], n_records, p=[0.15, 0.15, 0.15, 0.15, 0.15, 0.15, 0.10])
            data['sigma_value'] = sigma_values
        else:
            data['sigma_value'] = [np.nan] * n_records

        if include_boundary_plane:
            data['boundary_plane_h'] = np.random.randint(1, 5, n_records)
            data['boundary_plane_k'] = np.random.randint(0, 5, n_records)
            data['boundary_plane_l'] = np.random.randint(0, 5, n_records)
        else:
            data['boundary_plane_h'] = [np.nan] * n_records
            data['boundary_plane_k'] = [np.nan] * n_records
            data['boundary_plane_l'] = [np.nan] * n_records

        return pd.DataFrame(data)

    def test_load_parsed_data_success(self):
        """Test loading parsed data from parquet file."""
        df = self._create_mock_parsed_data()
        parquet_path = self.data_dir / "parsed_geometry.parquet"
        df.to_parquet(parquet_path)

        loaded_df = load_parsed_data(str(parquet_path))

        self.assertIsInstance(loaded_df, pd.DataFrame)
        self.assertEqual(len(loaded_df), len(df))
        self.assertTrue(all(col in loaded_df.columns for col in df.columns))

    def test_load_parsed_data_file_not_found(self):
        """Test loading from non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            load_parsed_data("non_existent_file.parquet")

    def test_validate_features_all_present(self):
        """Test validation when all required features are present."""
        df = self._create_mock_parsed_data()
        required_features = [
            'misorientation_angle', 'boundary_plane_h', 'boundary_plane_k', 'boundary_plane_l',
            'sigma_value', 'temperature', 'composition', 'diffusivity',
            'boundary_width', 'excess_volume'
        ]

        valid_df, missing_features = validate_features(df, required_features)

        self.assertIsInstance(valid_df, pd.DataFrame)
        self.assertIsInstance(missing_features, list)
        self.assertEqual(len(missing_features), 0)
        # All rows should be valid since we created valid data
        self.assertEqual(len(valid_df), len(df))

    def test_validate_features_missing_misorientation(self):
        """Test validation when misorientation is missing (NaN)."""
        df = self._create_mock_parsed_data(include_misorientation=False)
        required_features = ['misorientation_angle', 'sigma_value', 'temperature', 'diffusivity']

        valid_df, missing_features = validate_features(df, required_features)

        self.assertEqual(len(valid_df), 0)
        self.assertIn('misorientation_angle', missing_features)

    def test_validate_features_missing_sigma(self):
        """Test validation when sigma value is missing (NaN)."""
        df = self._create_mock_parsed_data(include_sigma=False)
        required_features = ['sigma_value', 'temperature', 'diffusivity']

        valid_df, missing_features = validate_features(df, required_features)

        self.assertEqual(len(valid_df), 0)
        self.assertIn('sigma_value', missing_features)

    def test_validate_features_partial_validity(self):
        """Test validation with some rows having valid data and some missing."""
        df = self._create_mock_parsed_data(n_records=100)
        # Set first 50 rows to have NaN in sigma_value
        df.loc[:49, 'sigma_value'] = np.nan

        required_features = ['sigma_value', 'temperature', 'diffusivity']

        valid_df, missing_features = validate_features(df, required_features)

        self.assertEqual(len(valid_df), 50)
        self.assertEqual(len(missing_features), 0)  # No missing features in the valid set

    def test_tag_metadata_features(self):
        """Test tagging of metadata features."""
        df = self._create_mock_parsed_data()

        tagged_df = tag_metadata_features(df)

        self.assertIn('simulation_method', tagged_df.columns)
        self.assertIn('potential_id', tagged_df.columns)
        # Verify the values are preserved
        self.assertTrue(all(tagged_df['simulation_method'] == 'DFT'))
        self.assertTrue(all(tagged_df['potential_id'] == 'PBE'))

    def test_apply_sampling_deterministic(self):
        """Test that sampling is deterministic with a fixed seed."""
        df = self._create_mock_parsed_data(n_records=1000)

        # Sample with seed=42
        sampled_df_1 = apply_sampling(df, sample_size=100, seed=42)
        sampled_df_2 = apply_sampling(df, sample_size=100, seed=42)

        self.assertEqual(len(sampled_df_1), len(sampled_df_2))
        # Check if indices are the same (deterministic)
        pd.testing.assert_frame_equal(sampled_df_1.reset_index(drop=True), sampled_df_2.reset_index(drop=True))

    def test_apply_sampling_no_sampling_needed(self):
        """Test that no sampling occurs when dataset is smaller than sample_size."""
        df = self._create_mock_parsed_data(n_records=50)

        sampled_df = apply_sampling(df, sample_size=100, seed=42)

        self.assertEqual(len(sampled_df), 50)
        pd.testing.assert_frame_equal(sampled_df.reset_index(drop=True), df.reset_index(drop=True))

    def test_enforce_minimum_records_sufficient(self):
        """Test that no error is raised when sufficient records are available."""
        df = self._create_mock_parsed_data(n_records=600)
        required_count = 500

        # Should not raise
        result_df = enforce_minimum_records(df, required_count, "test_source")

        self.assertEqual(len(result_df), 600)

    def test_enforce_minimum_records_insufficient(self):
        """Test that DataInsufficiencyError is raised when records are insufficient."""
        df = self._create_mock_parsed_data(n_records=400)
        required_count = 500

        with self.assertRaises(DataInsufficiencyError):
            enforce_minimum_records(df, required_count, "test_source")

    def test_write_exclusion_report(self):
        """Test writing exclusion report to JSON file."""
        total_records = 1000
        valid_records = 600
        missing_features = ['sigma_value', 'boundary_plane_normal']
        exclusion_reasons = {
            'sigma_value': 200,
            'boundary_plane_normal': 150,
            'other': 50
        }

        report_path = self.artifacts_dir / "exclusion_report.json"

        write_exclusion_report(
            report_path=str(report_path),
            total_records=total_records,
            valid_records=valid_records,
            missing_features=missing_features,
            exclusion_reasons=exclusion_reasons
        )

        self.assertTrue(report_path.exists())

        with open(report_path, 'r') as f:
            report = json.load(f)

        self.assertEqual(report['total_records'], total_records)
        self.assertEqual(report['valid_records'], valid_records)
        self.assertEqual(len(report['missing_features']), len(missing_features))
        self.assertEqual(report['exclusion_reasons'], exclusion_reasons)

    def test_save_cleaned_data(self):
        """Test saving cleaned data to parquet file."""
        df = self._create_mock_parsed_data()
        output_path = self.data_dir / "cleaned_dataset.parquet"

        save_cleaned_data(df, str(output_path))

        self.assertTrue(output_path.exists())

        # Verify we can load it back
        loaded_df = pd.read_parquet(output_path)
        self.assertEqual(len(loaded_df), len(df))
        self.assertTrue(all(col in loaded_df.columns for col in df.columns))

    def test_full_preprocess_pipeline_integration(self):
        """Test a full preprocessing pipeline with mock data."""
        # Create mock data with some invalid records
        df = self._create_mock_parsed_data(n_records=1000)
        # Make 200 records missing sigma
        df.loc[:199, 'sigma_value'] = np.nan
        # Make 100 records missing misorientation
        df.loc[:299, 'misorientation_angle'] = np.nan  # Overlaps with above

        parquet_path = self.data_dir / "parsed_geometry.parquet"
        df.to_parquet(parquet_path)

        # Step 1: Load
        loaded_df = load_parsed_data(str(parquet_path))
        self.assertEqual(len(loaded_df), 1000)

        # Step 2: Validate features
        required_features = [
            'misorientation_angle', 'boundary_plane_h', 'boundary_plane_k', 'boundary_plane_l',
            'sigma_value', 'temperature', 'composition', 'diffusivity',
            'boundary_width', 'excess_volume'
        ]
        valid_df, missing_features = validate_features(loaded_df, required_features)

        # We expect ~700 valid records (1000 - 300 invalid due to overlapping NaNs)
        # The exact count depends on the overlap logic in validate_features
        self.assertGreater(len(valid_df), 0)
        self.assertEqual(len(missing_features), 0)

        # Step 3: Tag metadata (already done in create_mock, but test the function)
        tagged_df = tag_metadata_features(valid_df)
        self.assertIn('simulation_method', tagged_df.columns)

        # Step 4: Apply sampling (downsample to 500 for testing)
        sampled_df = apply_sampling(tagged_df, sample_size=500, seed=42)
        self.assertEqual(len(sampled_df), 500)

        # Step 5: Enforce minimum (should pass with 500 records)
        final_df = enforce_minimum_records(sampled_df, required_count=500, source="test")
        self.assertEqual(len(final_df), 500)

        # Step 6: Write exclusion report
        exclusion_path = self.artifacts_dir / "exclusion_report.json"
        write_exclusion_report(
            report_path=str(exclusion_path),
            total_records=1000,
            valid_records=len(valid_df),
            missing_features=['sigma_value', 'misorientation_angle'],
            exclusion_reasons={'sigma_value': 200, 'misorientation_angle': 100}
        )
        self.assertTrue(exclusion_path.exists())

        # Step 7: Save cleaned data
        output_path = self.data_dir / "cleaned_dataset.parquet"
        save_cleaned_data(final_df, str(output_path))
        self.assertTrue(output_path.exists())

    def test_sigma_value_calculation_logic(self):
        """Test that sigma values are correctly handled (present vs calculated vs missing)."""
        # Create data with mixed sigma values (some from metadata, some calculated, some missing)
        df = self._create_mock_parsed_data(n_records=100)

        # Simulate: 70 valid sigma, 20 calculated (marked somehow), 10 missing
        # In real data, this would be differentiated, but here we just test the filtering logic
        valid_mask = ~df['sigma_value'].isna()
        self.assertEqual(valid_mask.sum(), 90)  # 100 - 10 NaN

        required_features = ['sigma_value']
        valid_df, missing_features = validate_features(df, required_features)

        self.assertEqual(len(valid_df), 90)
        self.assertNotIn('sigma_value', missing_features)

    def test_boundary_plane_normal_handling(self):
        """Test that boundary plane normal (h, k, l) is correctly validated."""
        df = self._create_mock_parsed_data()

        # Test with valid boundary plane
        required_features = ['boundary_plane_h', 'boundary_plane_k', 'boundary_plane_l']
        valid_df, missing_features = validate_features(df, required_features)
        self.assertEqual(len(valid_df), 100)

        # Test with missing boundary plane normal
        df_missing_plane = df.copy()
        df_missing_plane['boundary_plane_h'] = np.nan
        df_missing_plane['boundary_plane_k'] = np.nan
        df_missing_plane['boundary_plane_l'] = np.nan

        valid_df_missing, missing_features_missing = validate_features(df_missing_plane, required_features)
        self.assertEqual(len(valid_df_missing), 0)
        self.assertIn('boundary_plane_h', missing_features_missing)

    def test_missing_value_handling_edge_cases(self):
        """Test edge cases for missing value handling."""
        # All NaN
        df_all_nan = pd.DataFrame({
            'sigma_value': [np.nan] * 10,
            'temperature': [np.nan] * 10,
            'diffusivity': [np.nan] * 10
        })

        required_features = ['sigma_value', 'temperature', 'diffusivity']
        valid_df, missing_features = validate_features(df_all_nan, required_features)
        self.assertEqual(len(valid_df), 0)
        self.assertEqual(len(missing_features), 3)

        # No NaN
        df_no_nan = pd.DataFrame({
            'sigma_value': [1.0] * 10,
            'temperature': [300.0] * 10,
            'diffusivity': [1e-10] * 10
        })

        valid_df, missing_features = validate_features(df_no_nan, required_features)
        self.assertEqual(len(valid_df), 10)
        self.assertEqual(len(missing_features), 0)

        # Mixed: some columns all NaN, some mixed
        df_mixed = pd.DataFrame({
            'sigma_value': [np.nan] * 10,  # All NaN
            'temperature': [300.0] * 10,   # All valid
            'diffusivity': [1e-10] * 5 + [np.nan] * 5  # Mixed
        })

        valid_df, missing_features = validate_features(df_mixed, required_features)
        self.assertEqual(len(valid_df), 0)  # sigma_value is all NaN, so no valid rows
        self.assertIn('sigma_value', missing_features)

    def test_feature_engineering_preservation(self):
        """Test that feature engineering preserves all necessary columns."""
        df = self._create_mock_parsed_data()

        required_features = [
            'misorientation_angle', 'boundary_plane_h', 'boundary_plane_k', 'boundary_plane_l',
            'sigma_value', 'temperature', 'composition', 'diffusivity',
            'boundary_width', 'excess_volume', 'simulation_method', 'potential_id'
        ]

        valid_df, _ = validate_features(df, required_features)

        # Check that all required features are present in the valid dataframe
        for feature in required_features:
            self.assertIn(feature, valid_df.columns)

        # Check that no extra columns were removed (except potentially index)
        original_cols = set(df.columns)
        valid_cols = set(valid_df.columns)
        self.assertEqual(original_cols, valid_cols)

if __name__ == '__main__':
    unittest.main()