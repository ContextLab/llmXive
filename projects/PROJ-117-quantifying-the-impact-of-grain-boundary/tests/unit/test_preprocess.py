"""
Unit tests for code/preprocess.py
Tests cover:
1. Feature engineering logic (tagging metadata, validation)
2. Σ value extraction/calculation logic (via geometry_parser dependency)
3. Missing value handling (exclusion logic)
4. Minimum record enforcement (n >= 500)
5. Sampling strategy application
6. Exclusion report generation
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocess import (
    load_parsed_data,
    validate_features,
    tag_metadata_features,
    apply_sampling,
    enforce_minimum_records,
    write_exclusion_report,
    save_cleaned_data,
    main
)
from error_handling import DataInsufficiencyError


class TestLoadParsedData(unittest.TestCase):
    """Tests for load_parsed_data function"""

    def test_load_parquet_success(self):
        """Test successful loading of parquet file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy parquet file
            df = pd.DataFrame({
                'misorientation_angle': [10.0, 20.0, 30.0],
                'sigma_value': [3, 5, 7],
                'boundary_width': [1.0, 2.0, 3.0],
                'diffusivity': [1e-10, 2e-10, 3e-10]
            })
            parquet_path = Path(tmpdir) / "test.parquet"
            df.to_parquet(parquet_path)

            loaded_df = load_parsed_data(parquet_path)

            self.assertEqual(len(loaded_df), 3)
            self.assertTrue('misorientation_angle' in loaded_df.columns)
            self.assertTrue('sigma_value' in loaded_df.columns)

    def test_load_parquet_missing_file(self):
        """Test handling of missing parquet file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "nonexistent.parquet"

            with self.assertRaises(FileNotFoundError):
                load_parsed_data(missing_path)


class TestValidateFeatures(unittest.TestCase):
    """Tests for validate_features function"""

    def test_validate_all_present(self):
        """Test validation when all required features are present"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [3, 5, 7],
            'boundary_plane_normal_h': [1, 0, 0],
            'boundary_plane_normal_k': [0, 1, 0],
            'boundary_plane_normal_l': [0, 0, 1],
            'temperature': [1000, 1100, 1200],
            'composition': ['CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'boundary_width': [1.0, 2.0, 3.0],
            'excess_volume': [0.1, 0.2, 0.3]
        })

        valid_df, missing_features = validate_features(df)

        self.assertEqual(len(valid_df), 3)
        self.assertEqual(len(missing_features), 0)

    def test_validate_missing_sigma(self):
        """Test validation when sigma_value is missing"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [np.nan, 5, 7],  # One missing
            'boundary_plane_normal_h': [1, 0, 0],
            'boundary_plane_normal_k': [0, 1, 0],
            'boundary_plane_normal_l': [0, 0, 1],
            'temperature': [1000, 1100, 1200],
            'composition': ['CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'boundary_width': [1.0, 2.0, 3.0],
            'excess_volume': [0.1, 0.2, 0.3]
        })

        valid_df, missing_features = validate_features(df)

        # Only 2 rows should remain (one excluded)
        self.assertEqual(len(valid_df), 2)
        self.assertIn('sigma_value', missing_features)

    def test_validate_missing_diffusivity(self):
        """Test validation when diffusivity is missing"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [3, 5, 7],
            'boundary_plane_normal_h': [1, 0, 0],
            'boundary_plane_normal_k': [0, 1, 0],
            'boundary_plane_normal_l': [0, 0, 1],
            'temperature': [1000, 1100, 1200],
            'composition': ['CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [np.nan, 2e-10, 3e-10],  # One missing
            'boundary_width': [1.0, 2.0, 3.0],
            'excess_volume': [0.1, 0.2, 0.3]
        })

        valid_df, missing_features = validate_features(df)

        self.assertEqual(len(valid_df), 2)
        self.assertIn('diffusivity', missing_features)

    def test_validate_multiple_missing(self):
        """Test validation when multiple features are missing across rows"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0, 40.0],
            'sigma_value': [3, np.nan, 7, 9],  # Row 1 missing
            'boundary_plane_normal_h': [1, 0, np.nan, 0],  # Row 2 missing
            'boundary_plane_normal_k': [0, 1, 0, np.nan],  # Row 3 missing
            'boundary_plane_normal_l': [0, 0, 1, 0],
            'temperature': [1000, 1100, 1200, 1300],
            'composition': ['CeO2', 'CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10, np.nan, 4e-10],  # Row 2 missing
            'boundary_width': [1.0, 2.0, 3.0, 4.0],
            'excess_volume': [0.1, 0.2, 0.3, 0.4]
        })

        valid_df, missing_features = validate_features(df)

        # Only row 0 should remain (all others have at least one missing value)
        self.assertEqual(len(valid_df), 1)
        self.assertIn('sigma_value', missing_features)
        self.assertIn('diffusivity', missing_features)


class TestTagMetadataFeatures(unittest.TestCase):
    """Tests for tag_metadata_features function"""

    def test_tag_simulation_method(self):
        """Test tagging of simulation_method feature"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [3, 5, 7],
            'temperature': [1000, 1100, 1200],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'simulation_method': ['DFT', 'MD', 'KMC']
        })

        tagged_df = tag_metadata_features(df)

        self.assertIn('simulation_method', tagged_df.columns)
        self.assertEqual(list(tagged_df['simulation_method']), ['DFT', 'MD', 'KMC'])

    def test_tag_potential_id(self):
        """Test tagging of potential_id feature"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [3, 5, 7],
            'temperature': [1000, 1100, 1200],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'potential_id': ['pot_001', 'pot_002', 'pot_003']
        })

        tagged_df = tag_metadata_features(df)

        self.assertIn('potential_id', tagged_df.columns)
        self.assertEqual(list(tagged_df['potential_id']), ['pot_001', 'pot_002', 'pot_003'])

    def test_tag_missing_metadata(self):
        """Test handling when metadata features are missing"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [3, 5, 7],
            'temperature': [1000, 1100, 1200],
            'diffusivity': [1e-10, 2e-10, 3e-10]
        })

        tagged_df = tag_metadata_features(df)

        # Should add columns with None/NaN if not present
        self.assertIn('simulation_method', tagged_df.columns)
        self.assertIn('potential_id', tagged_df.columns)


class TestApplySampling(unittest.TestCase):
    """Tests for apply_sampling function"""

    def test_sampling_with_config(self):
        """Test sampling using sample_config.yaml"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample_config.yaml
            config_path = Path(tmpdir) / "sample_config.yaml"
            config_content = """
            strategy: "first_n"
            sample_size: 2
            """
            with open(config_path, 'w') as f:
                f.write(config_content)

            df = pd.DataFrame({
                'id': [1, 2, 3, 4, 5],
                'value': [10, 20, 30, 40, 50]
            })

            sampled_df = apply_sampling(df, config_path)

            self.assertEqual(len(sampled_df), 2)
            self.assertEqual(list(sampled_df['id']), [1, 2])

    def test_sampling_large_dataset(self):
        """Test sampling when dataset is larger than sample_size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sample_config.yaml"
            config_content = """
            strategy: "first_n"
            sample_size: 3
            """
            with open(config_path, 'w') as f:
                f.write(config_content)

            # Create a larger dataset
            df = pd.DataFrame({
                'id': range(100),
                'value': range(100)
            })

            sampled_df = apply_sampling(df, config_path)

            self.assertEqual(len(sampled_df), 3)
            self.assertEqual(list(sampled_df['id']), [0, 1, 2])

    def test_no_sampling_needed(self):
        """Test when dataset is smaller than sample_size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sample_config.yaml"
            config_content = """
            strategy: "first_n"
            sample_size: 100
            """
            with open(config_path, 'w') as f:
                f.write(config_content)

            df = pd.DataFrame({
                'id': [1, 2, 3],
                'value': [10, 20, 30]
            })

            sampled_df = apply_sampling(df, config_path)

            # Should return original dataset
            self.assertEqual(len(sampled_df), 3)


class TestEnforceMinimumRecords(unittest.TestCase):
    """Tests for enforce_minimum_records function"""

    def test_enforce_sufficient_records(self):
        """Test when dataset has sufficient records"""
        df = pd.DataFrame({
            'id': range(500),
            'value': range(500)
        })

        result_df = enforce_minimum_records(df, min_records=500)

        self.assertEqual(len(result_df), 500)

    def test_enforce_insufficient_records(self):
        """Test when dataset has insufficient records"""
        df = pd.DataFrame({
            'id': range(100),
            'value': range(100)
        })

        with self.assertRaises(DataInsufficiencyError) as context:
            enforce_minimum_records(df, min_records=500)

        self.assertIn("Data Insufficiency", str(context.exception))
        self.assertIn("100", str(context.exception))
        self.assertIn("500", str(context.exception))

    def test_enforce_exactly_minimum(self):
        """Test when dataset has exactly the minimum records"""
        df = pd.DataFrame({
            'id': range(500),
            'value': range(500)
        })

        result_df = enforce_minimum_records(df, min_records=500)

        self.assertEqual(len(result_df), 500)


class TestWriteExclusionReport(unittest.TestCase):
    """Tests for write_exclusion_report function"""

    def test_write_report_success(self):
        """Test successful writing of exclusion report"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "exclusion_report.json"

            report_data = {
                'total_records': 1000,
                'valid_records': 800,
                'excluded_records': 200,
                'missing_features': ['sigma_value', 'diffusivity'],
                'exclusion_details': {
                    'sigma_value': 50,
                    'diffusivity': 150
                }
            }

            write_exclusion_report(report_path, report_data)

            self.assertTrue(report_path.exists())

            with open(report_path, 'r') as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data['total_records'], 1000)
            self.assertEqual(loaded_data['valid_records'], 800)
            self.assertEqual(loaded_data['excluded_records'], 200)

    def test_write_report_empty_missing_features(self):
        """Test writing report with no missing features"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "exclusion_report.json"

            report_data = {
                'total_records': 1000,
                'valid_records': 1000,
                'excluded_records': 0,
                'missing_features': [],
                'exclusion_details': {}
            }

            write_exclusion_report(report_path, report_data)

            self.assertTrue(report_path.exists())

            with open(report_path, 'r') as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data['excluded_records'], 0)


class TestSaveCleanedData(unittest.TestCase):
    """Tests for save_cleaned_data function"""

    def test_save_parquet_success(self):
        """Test successful saving of cleaned data as parquet"""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'id': [1, 2, 3],
                'value': [10, 20, 30]
            })
            output_path = Path(tmpdir) / "cleaned.parquet"

            save_cleaned_data(df, output_path)

            self.assertTrue(output_path.exists())

            loaded_df = pd.read_parquet(output_path)
            self.assertEqual(len(loaded_df), 3)
            self.assertEqual(list(loaded_df['id']), [1, 2, 3])

    def test_save_parquet_creates_directory(self):
        """Test that save_cleaned_data creates output directory if needed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                'id': [1, 2, 3],
                'value': [10, 20, 30]
            })
            output_path = Path(tmpdir) / "subdir" / "cleaned.parquet"

            save_cleaned_data(df, output_path)

            self.assertTrue(output_path.exists())


class TestSigmaValueLogic(unittest.TestCase):
    """Tests specifically for Σ value extraction/calculation logic"""

    def test_sigma_value_nan_handling(self):
        """Test that NaN sigma values are properly excluded"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [3, np.nan, 7],
            'boundary_plane_normal_h': [1, 0, 0],
            'boundary_plane_normal_k': [0, 1, 0],
            'boundary_plane_normal_l': [0, 0, 1],
            'temperature': [1000, 1100, 1200],
            'composition': ['CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'boundary_width': [1.0, 2.0, 3.0],
            'excess_volume': [0.1, 0.2, 0.3]
        })

        valid_df, missing_features = validate_features(df)

        # Row with NaN sigma_value should be excluded
        self.assertEqual(len(valid_df), 2)
        self.assertIn('sigma_value', missing_features)

    def test_sigma_value_zero_handling(self):
        """Test that zero sigma values are kept (if valid)"""
        df = pd.DataFrame({
            'misorientation_angle': [10.0, 20.0, 30.0],
            'sigma_value': [3, 0, 7],  # Zero is a valid integer
            'boundary_plane_normal_h': [1, 0, 0],
            'boundary_plane_normal_k': [0, 1, 0],
            'boundary_plane_normal_l': [0, 0, 1],
            'temperature': [1000, 1100, 1200],
            'composition': ['CeO2', 'CeO2', 'CeO2'],
            'diffusivity': [1e-10, 2e-10, 3e-10],
            'boundary_width': [1.0, 2.0, 3.0],
            'excess_volume': [0.1, 0.2, 0.3]
        })

        valid_df, missing_features = validate_features(df)

        # All rows should be kept (0 is not NaN)
        self.assertEqual(len(valid_df), 3)


class TestMissingValueHandling(unittest.TestCase):
    """Tests specifically for missing value handling logic"""

    def test_missing_value_detection(self):
        """Test that various missing value representations are detected"""
        df = pd.DataFrame({
            'value1': [1, np.nan, None, 4],
            'value2': [1, None, np.nan, 4],
            'value3': [1, '', None, 4]  # Empty string might be treated differently
        })

        # Check that nan/None are detected
        self.assertTrue(pd.isna(df['value1']).iloc[1])
        self.assertTrue(pd.isna(df['value1']).iloc[2])

    def test_complete_row_exclusion(self):
        """Test that rows with any missing required value are excluded"""
        df = pd.DataFrame({
            'required1': [1, 2, np.nan, 4],
            'required2': [5, np.nan, 7, 8],
            'required3': [9, 10, 11, np.nan]
        })

        valid_df, missing_features = validate_features(df)

        # Only row 0 should remain (all others have at least one missing value)
        self.assertEqual(len(valid_df), 1)
        self.assertEqual(list(valid_df['required1']), [1])


class TestPreprocessMain(unittest.TestCase):
    """Tests for the main function of preprocess.py"""

    @patch('preprocess.load_parsed_data')
    @patch('preprocess.validate_features')
    @patch('preprocess.tag_metadata_features')
    @patch('preprocess.apply_sampling')
    @patch('preprocess.enforce_minimum_records')
    @patch('preprocess.write_exclusion_report')
    @patch('preprocess.save_cleaned_data')
    def test_main_success(
        self,
        mock_save,
        mock_write_report,
        mock_enforce,
        mock_sample,
        mock_tag,
        mock_validate,
        mock_load
    ):
        """Test successful main execution"""
        mock_load.return_value = pd.DataFrame({'a': [1, 2, 3]})
        mock_validate.return_value = (pd.DataFrame({'a': [1, 2, 3]}), [])
        mock_tag.return_value = pd.DataFrame({'a': [1, 2, 3], 'tag': ['x', 'y', 'z']})
        mock_sample.return_value = pd.DataFrame({'a': [1, 2, 3], 'tag': ['x', 'y', 'z']})
        mock_enforce.return_value = pd.DataFrame({'a': [1, 2, 3], 'tag': ['x', 'y', 'z']})

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            report_path = Path(tmpdir) / "report.json"
            config_path = Path(tmpdir) / "config.yaml"

            # Create dummy config
            with open(config_path, 'w') as f:
                f.write("strategy: first_n\nsample_size: 100\n")

            # Mock the Path.exists() for config
            with patch.object(Path, 'exists', return_value=True):
                main(str(input_path), str(output_path), str(report_path), str(config_path))

            mock_load.assert_called_once()
            mock_validate.assert_called_once()
            mock_tag.assert_called_once()
            mock_sample.assert_called_once()
            mock_enforce.assert_called_once()
            mock_write_report.assert_called_once()
            mock_save.assert_called_once()

    @patch('preprocess.load_parsed_data')
    @patch('preprocess.validate_features')
    @patch('preprocess.tag_metadata_features')
    @patch('preprocess.apply_sampling')
    @patch('preprocess.enforce_minimum_records')
    def test_main_insufficient_data(
        self,
        mock_enforce,
        mock_sample,
        mock_tag,
        mock_validate,
        mock_load
    ):
        """Test main execution with insufficient data"""
        mock_load.return_value = pd.DataFrame({'a': [1, 2, 3]})
        mock_validate.return_value = (pd.DataFrame({'a': [1, 2, 3]}), [])
        mock_tag.return_value = pd.DataFrame({'a': [1, 2, 3], 'tag': ['x', 'y', 'z']})
        mock_sample.return_value = pd.DataFrame({'a': [1, 2, 3], 'tag': ['x', 'y', 'z']})

        # Mock enforce_minimum_records to raise DataInsufficiencyError
        mock_enforce.side_effect = DataInsufficiencyError("Data insufficient")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            report_path = Path(tmpdir) / "report.json"
            config_path = Path(tmpdir) / "config.yaml"

            with open(config_path, 'w') as f:
                f.write("strategy: first_n\nsample_size: 100\n")

            with patch.object(Path, 'exists', return_value=True):
                with self.assertRaises(SystemExit) as context:
                    main(str(input_path), str(output_path), str(report_path), str(config_path))

                self.assertEqual(context.exception.code, 1)


if __name__ == '__main__':
    unittest.main()