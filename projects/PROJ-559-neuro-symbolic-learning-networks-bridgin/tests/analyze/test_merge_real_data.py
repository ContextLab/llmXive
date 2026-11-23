"""
Tests for the merge_real_data module.

These tests verify the logic for merging simulated and real student data,
validating data source effects, and handling edge cases.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analyze.merge_real_data import (
    load_real_student_data,
    load_simulated_data,
    validate_data_source_effects,
    merge_datasets,
    save_merged_data,
    save_validation_report,
    MIN_RECORDS_THRESHOLD
)

class TestLoadRealStudentData:
    """Tests for load_real_student_data function"""

    def test_load_real_data_success(self, tmp_path):
        """Test successful loading of real student data"""
        # Create test data
        test_data = {
            'problem_id': [1, 2, 3],
            'condition': ['neural', 'symbolic', 'neuro_symbolic'],
            'correct': [1, 0, 1],
            'rt_seconds': [10.5, 12.3, 8.7],
            'comprehension_rating': [4, 3, 5]
        }
        df = pd.DataFrame(test_data)

        # Save to temporary file
        test_file = tmp_path / "real_data.csv"
        df.to_csv(test_file, index=False)

        # Load and verify
        loaded_df = load_real_student_data(str(test_file))
        assert len(loaded_df) == 3
        assert 'data_source' not in loaded_df.columns  # Should not have data_source yet

    def test_load_real_data_missing_file(self, tmp_path):
        """Test error when real data file is missing"""
        with pytest.raises(FileNotFoundError):
            load_real_student_data(str(tmp_path / "nonexistent.csv"))

    def test_load_real_data_missing_columns(self, tmp_path):
        """Test error when required columns are missing"""
        test_data = {
            'problem_id': [1, 2, 3],
            'condition': ['neural', 'symbolic', 'neuro_symbolic']
            # Missing required columns
        }
        df = pd.DataFrame(test_data)

        test_file = tmp_path / "real_data.csv"
        df.to_csv(test_file, index=False)

        with pytest.raises(ValueError, match="Real data missing required columns"):
            load_real_student_data(str(test_file))

class TestLoadSimulatedData:
    """Tests for load_simulated_data function"""

    def test_load_simulated_data_success(self, tmp_path):
        """Test successful loading of simulated student data"""
        test_data = {
            'problem_id': [1, 2, 3],
            'condition': ['neural', 'symbolic', 'neuro_symbolic'],
            'correct': [1, 0, 1],
            'rt_seconds': [10.5, 12.3, 8.7],
            'comprehension_rating': [4, 3, 5],
            'data_source': ['simulated', 'simulated', 'simulated']
        }
        df = pd.DataFrame(test_data)

        test_file = tmp_path / "sim_data.csv"
        df.to_csv(test_file, index=False)

        loaded_df = load_simulated_data(str(test_file))
        assert len(loaded_df) == 3
        assert 'data_source' in loaded_df.columns

    def test_load_simulated_data_missing_file(self, tmp_path):
        """Test error when simulated data file is missing"""
        with pytest.raises(FileNotFoundError):
            load_simulated_data(str(tmp_path / "nonexistent.csv"))

class TestMergeDatasets:
    """Tests for merge_datasets function"""

    def test_merge_with_real_and_simulated(self, tmp_path):
        """Test merging real and simulated data"""
        # Create real data
        real_data = {
            'problem_id': [1, 2],
            'condition': ['neural', 'symbolic'],
            'correct': [1, 0],
            'rt_seconds': [10.5, 12.3],
            'comprehension_rating': [4, 3]
        }
        real_df = pd.DataFrame(real_data)

        # Create simulated data
        sim_data = {
            'problem_id': [3, 4],
            'condition': ['neuro_symbolic', 'neural'],
            'correct': [1, 1],
            'rt_seconds': [9.1, 11.2],
            'comprehension_rating': [5, 4],
            'data_source': ['simulated', 'simulated']
        }
        sim_df = pd.DataFrame(sim_data)

        # Merge
        merged = merge_datasets(real_df, sim_df)

        assert len(merged) == 4
        assert 'data_source' in merged.columns
        assert merged['data_source'].value_counts()['real'] == 2
        assert merged['data_source'].value_counts()['simulated'] == 2

    def test_merge_handles_missing_columns(self, tmp_path):
        """Test that merge handles datasets with different columns"""
        # Real data missing some columns
        real_data = {
            'problem_id': [1],
            'condition': ['neural'],
            'correct': [1]
        }
        real_df = pd.DataFrame(real_data)

        # Simulated data with all columns
        sim_data = {
            'problem_id': [2],
            'condition': ['symbolic'],
            'correct': [0],
            'rt_seconds': [10.0],
            'comprehension_rating': [3],
            'data_source': ['simulated']
        }
        sim_df = pd.DataFrame(sim_data)

        merged = merge_datasets(real_df, sim_df)
        assert len(merged) == 2
        assert 'rt_seconds' in merged.columns
        assert pd.isna(merged.loc[0, 'rt_seconds'])  # Real data should have NaN for missing column

class TestValidateDataSourceEffects:
    """Tests for validate_data_source_effects function"""

    def test_validation_passes_with_sufficient_real_data(self, tmp_path):
        """Test validation passes when real data meets threshold"""
        # Create merged data with enough real records
        data = []
        for i in range(MIN_RECORDS_THRESHOLD + 10):
            data.append({
                'problem_id': i,
                'condition': 'neural',
                'correct': 1,
                'rt_seconds': 10.0,
                'comprehension_rating': 4,
                'data_source': 'real'
            })
        for i in range(100):
            data.append({
                'problem_id': i + MIN_RECORDS_THRESHOLD + 10,
                'condition': 'symbolic',
                'correct': 0,
                'rt_seconds': 12.0,
                'comprehension_rating': 3,
                'data_source': 'simulated'
            })

        merged_df = pd.DataFrame(data)
        is_valid, details = validate_data_source_effects(merged_df)

        assert is_valid
        assert details['meets_minimum_threshold'] is True
        assert details['real_records'] >= MIN_RECORDS_THRESHOLD
        assert len(details['issues']) == 0

    def test_validation_fails_with_insufficient_real_data(self, tmp_path):
        """Test validation fails when real data is below threshold"""
        # Create merged data with insufficient real records
        data = []
        for i in range(MIN_RECORDS_THRESHOLD - 10):
            data.append({
                'problem_id': i,
                'condition': 'neural',
                'correct': 1,
                'rt_seconds': 10.0,
                'comprehension_rating': 4,
                'data_source': 'real'
            })
        for i in range(100):
            data.append({
                'problem_id': i + MIN_RECORDS_THRESHOLD - 10,
                'condition': 'symbolic',
                'correct': 0,
                'rt_seconds': 12.0,
                'comprehension_rating': 3,
                'data_source': 'simulated'
            })

        merged_df = pd.DataFrame(data)
        is_valid, details = validate_data_source_effects(merged_df)

        assert not is_valid
        assert details['meets_minimum_threshold'] is False
        assert any("below minimum threshold" in issue for issue in details['issues'])

    def test_validation_fails_with_missing_data_source(self, tmp_path):
        """Test validation fails when data_source column is missing"""
        data = {
            'problem_id': [1, 2],
            'condition': ['neural', 'symbolic'],
            'correct': [1, 0]
        }
        merged_df = pd.DataFrame(data)

        is_valid, details = validate_data_source_effects(merged_df)

        assert not is_valid
        assert any("Missing 'data_source' column" in issue for issue in details['issues'])

    def test_validation_detects_null_data_source(self, tmp_path):
        """Test validation detects null values in data_source"""
        data = [
            {'problem_id': 1, 'condition': 'neural', 'correct': 1, 'rt_seconds': 10.0, 'comprehension_rating': 4, 'data_source': 'real'},
            {'problem_id': 2, 'condition': 'symbolic', 'correct': 0, 'rt_seconds': 12.0, 'comprehension_rating': 3, 'data_source': None}
        ]
        merged_df = pd.DataFrame(data)

        is_valid, details = validate_data_source_effects(merged_df)

        assert not is_valid
        assert any("null values" in issue for issue in details['issues'])

class TestSaveMergedData:
    """Tests for save_merged_data function"""

    def test_save_merged_data_creates_file(self, tmp_path):
        """Test that save_merged_data creates the output file"""
        df = pd.DataFrame({
            'problem_id': [1, 2],
            'condition': ['neural', 'symbolic'],
            'correct': [1, 0],
            'data_source': ['real', 'simulated']
        })

        output_path = tmp_path / "merged_data.csv"
        save_merged_data(df, str(output_path))

        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2

    def test_save_creates_directories(self, tmp_path):
        """Test that save_merged_data creates necessary directories"""
        df = pd.DataFrame({
            'problem_id': [1],
            'condition': ['neural'],
            'correct': [1]
        })

        output_path = tmp_path / "subdir" / "nested" / "merged_data.csv"
        save_merged_data(df, str(output_path))

        assert output_path.exists()

class TestSaveValidationReport:
    """Tests for save_validation_report function"""

    def test_save_validation_report_creates_file(self, tmp_path):
        """Test that save_validation_report creates the output file"""
        details = {
            'total_records': 10,
            'real_records': 5,
            'simulated_records': 5,
            'meets_minimum_threshold': False,
            'issues': ['Test issue']
        }

        output_path = tmp_path / "validation_report.json"
        save_validation_report(details, str(output_path))

        assert output_path.exists()
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded['total_records'] == 10
        assert 'Test issue' in loaded['issues']

class TestIntegration:
    """Integration tests for the full merge pipeline"""

    def test_full_merge_pipeline(self, tmp_path):
        """Test complete merge workflow"""
        # Create real data
        real_data = []
        for i in range(250):
            real_data.append({
                'problem_id': i,
                'condition': ['neural', 'symbolic', 'neuro_symbolic'][i % 3],
                'correct': i % 2,
                'rt_seconds': 10.0 + (i % 5),
                'comprehension_rating': (i % 5) + 1
            })
        real_df = pd.DataFrame(real_data)

        # Create simulated data
        sim_data = []
        for i in range(150):
            sim_data.append({
                'problem_id': i + 250,
                'condition': ['neural', 'symbolic', 'neuro_symbolic'][i % 3],
                'correct': i % 2,
                'rt_seconds': 12.0 + (i % 5),
                'comprehension_rating': (i % 5) + 1,
                'data_source': 'simulated'
            })
        sim_df = pd.DataFrame(sim_data)

        # Save to temp files
        real_file = tmp_path / "real.csv"
        sim_file = tmp_path / "sim.csv"
        merged_file = tmp_path / "merged.csv"
        report_file = tmp_path / "report.json"

        real_df.to_csv(real_file, index=False)
        sim_df.to_csv(sim_file, index=False)

        # Load and merge
        loaded_real = load_real_student_data(str(real_file))
        loaded_sim = load_simulated_data(str(sim_file))
        merged = merge_datasets(loaded_real, loaded_sim)

        # Validate
        is_valid, details = validate_data_source_effects(merged)

        # Save outputs
        save_merged_data(merged, str(merged_file))
        save_validation_report(details, str(report_file))

        # Verify results
        assert merged_file.exists()
        assert report_file.exists()
        assert is_valid
        assert details['total_records'] == 400
        assert details['real_records'] == 250
        assert details['simulated_records'] == 150
        assert details['meets_minimum_threshold'] is True