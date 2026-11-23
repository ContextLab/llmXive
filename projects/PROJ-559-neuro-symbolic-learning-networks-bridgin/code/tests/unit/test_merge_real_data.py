"""
Unit tests for merge_real_data.py

Tests:
- load_real_student_data
- load_simulated_data
- validate_data_source_effects
- merge_datasets
- save_merged_data
- save_validation_report
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analyze.merge_real_data import (
    load_real_student_data,
    load_simulated_data,
    validate_data_source_effects,
    merge_datasets,
    save_merged_data,
    save_validation_report
)


class TestLoadRealStudentData:
    """Tests for load_real_student_data function."""

    def test_load_real_data_success(self, tmp_path):
        """Test successful loading of real student data."""
        # Create a temporary CSV file
        csv_path = tmp_path / "real_data.csv"
        data = {
            'problem_id': ['prob_001', 'prob_002'],
            'condition': ['neural', 'symbolic'],
            'correct': [1, 0],
            'rt_seconds': [12.5, 18.3],
            'comprehension_rating': [4, 2]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Load the data
        result = load_real_student_data(str(csv_path))

        # Assertions
        assert len(result) == 2
        assert 'data_source' in result.columns
        assert all(result['data_source'] == 'real')
        assert 'problem_id' in result.columns
        assert 'correct' in result.columns

    def test_load_real_data_missing_file(self):
        """Test loading from a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_real_student_data("/non/existent/path.csv")

    def test_load_real_data_missing_columns(self, tmp_path):
        """Test loading data with missing required columns raises ValueError."""
        csv_path = tmp_path / "incomplete_data.csv"
        data = {
            'problem_id': ['prob_001'],
            'condition': ['neural']
            # Missing 'correct', 'rt_seconds', etc.
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_real_student_data(str(csv_path))


class TestLoadSimulatedData:
    """Tests for load_simulated_data function."""

    def test_load_simulated_data_success(self, tmp_path):
        """Test successful loading of simulated student data."""
        csv_path = tmp_path / "simulated_data.csv"
        data = {
            'student_id': ['sim_001', 'sim_002'],
            'problem_id': ['prob_001', 'prob_002'],
            'condition': ['neural', 'symbolic'],
            'correct': [1, 0],
            'rt_seconds': [12.5, 18.3],
            'comprehension_rating': [4, 2]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        result = load_simulated_data(str(csv_path))

        assert len(result) == 2
        assert 'data_source' in result.columns
        assert all(result['data_source'] == 'simulated')
        assert 'student_id' in result.columns

    def test_load_simulated_data_missing_file(self):
        """Test loading from a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_simulated_data("/non/existent/path.csv")

    def test_load_simulated_data_missing_columns(self, tmp_path):
        """Test loading data with missing required columns raises ValueError."""
        csv_path = tmp_path / "incomplete_sim.csv"
        data = {
            'student_id': ['sim_001'],
            'problem_id': ['prob_001']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_simulated_data(str(csv_path))


class TestValidateDataSourceEffects:
    """Tests for validate_data_source_effects function."""

    def test_validate_with_both_sources(self):
        """Test validation with both real and simulated data."""
        data = {
            'problem_id': ['prob_001', 'prob_002', 'prob_003'],
            'condition': ['neural', 'symbolic', 'neuro_symbolic'],
            'correct': [1, 0, 1],
            'rt_seconds': [12.5, 18.3, 15.0],
            'comprehension_rating': [4, 2, 5],
            'data_source': ['real', 'real', 'simulated']
        }
        df = pd.DataFrame(data)

        result = validate_data_source_effects(df)

        assert result['total_records'] == 3
        assert result['real_records'] == 2
        assert result['simulated_records'] == 1
        assert 'meets_minimum_threshold' in result
        assert 'issues' in result

    def test_validate_below_threshold(self):
        """Test validation when total records are below minimum threshold."""
        data = {
            'problem_id': ['prob_001'],
            'condition': ['neural'],
            'correct': [1],
            'rt_seconds': [12.5],
            'comprehension_rating': [4],
            'data_source': ['real']
        }
        df = pd.DataFrame(data)

        result = validate_data_source_effects(df)

        assert result['total_records'] == 1
        assert result['meets_minimum_threshold'] is False
        assert any("below minimum threshold" in issue for issue in result['issues'])

    def test_validate_missing_values(self):
        """Test validation detects missing values in key columns."""
        data = {
            'problem_id': ['prob_001', 'prob_002'],
            'condition': ['neural', 'symbolic'],
            'correct': [1, None],  # Missing value
            'rt_seconds': [12.5, 18.3],
            'comprehension_rating': [4, 2],
            'data_source': ['real', 'real']
        }
        df = pd.DataFrame(data)

        result = validate_data_source_effects(df)

        assert result['column_completeness']['correct']['missing_count'] == 1
        assert any("missing values" in issue for issue in result['issues'])


class TestMergeDatasets:
    """Tests for merge_datasets function."""

    def test_merge_real_and_simulated(self):
        """Test merging real and simulated datasets."""
        real_data = {
            'problem_id': ['prob_001', 'prob_002'],
            'condition': ['neural', 'symbolic'],
            'correct': [1, 0],
            'rt_seconds': [12.5, 18.3],
            'comprehension_rating': [4, 2],
            'data_source': ['real', 'real']
        }
        simulated_data = {
            'problem_id': ['prob_003', 'prob_004'],
            'condition': ['neuro_symbolic', 'neural'],
            'correct': [1, 1],
            'rt_seconds': [15.0, 10.2],
            'comprehension_rating': [5, 4],
            'data_source': ['simulated', 'simulated']
        }

        real_df = pd.DataFrame(real_data)
        simulated_df = pd.DataFrame(simulated_data)

        merged = merge_datasets(real_df, simulated_df)

        assert len(merged) == 4
        assert list(merged['data_source'].value_counts().keys()) == ['real', 'simulated']
        assert 'student_id' not in merged.columns  # Should be dropped during merge

    def test_merge_with_different_conditions(self):
        """Test merging datasets with different condition distributions."""
        real_data = {
            'problem_id': ['prob_001'],
            'condition': ['neural'],
            'correct': [1],
            'rt_seconds': [12.5],
            'comprehension_rating': [4],
            'data_source': ['real']
        }
        simulated_data = {
            'problem_id': ['prob_002'],
            'condition': ['symbolic'],
            'correct': [0],
            'rt_seconds': [18.3],
            'comprehension_rating': [2],
            'data_source': ['simulated']
        }

        real_df = pd.DataFrame(real_data)
        simulated_df = pd.DataFrame(simulated_data)

        merged = merge_datasets(real_df, simulated_df)

        assert len(merged) == 2
        assert set(merged['condition'].unique()) == {'neural', 'symbolic'}


class TestSaveMergedData:
    """Tests for save_merged_data function."""

    def test_save_merged_data_success(self, tmp_path):
        """Test successful saving of merged data."""
        data = {
            'problem_id': ['prob_001', 'prob_002'],
            'condition': ['neural', 'symbolic'],
            'correct': [1, 0],
            'rt_seconds': [12.5, 18.3],
            'comprehension_rating': [4, 2],
            'data_source': ['real', 'simulated']
        }
        df = pd.DataFrame(data)

        output_path = tmp_path / "merged_output.csv"
        result_path = save_merged_data(df, str(output_path))

        assert os.path.exists(result_path)
        loaded_df = pd.read_csv(result_path)
        assert len(loaded_df) == 2

    def test_save_creates_directories(self, tmp_path):
        """Test that save_merged_data creates necessary directories."""
        data = {
            'problem_id': ['prob_001'],
            'condition': ['neural'],
            'correct': [1],
            'rt_seconds': [12.5],
            'comprehension_rating': [4],
            'data_source': ['real']
        }
        df = pd.DataFrame(data)

        nested_path = tmp_path / "subdir1" / "subdir2" / "output.csv"
        result_path = save_merged_data(df, str(nested_path))

        assert os.path.exists(result_path)


class TestSaveValidationReport:
    """Tests for save_validation_report function."""

    def test_save_report_success(self, tmp_path):
        """Test successful saving of validation report."""
        report = {
            'total_records': 100,
            'real_records': 50,
            'simulated_records': 50,
            'meets_minimum_threshold': True,
            'issues': []
        }

        output_path = tmp_path / "validation_report.json"
        result_path = save_validation_report(report, str(output_path))

        assert os.path.exists(result_path)
        with open(result_path, 'r') as f:
            loaded_report = json.load(f)
        assert loaded_report['total_records'] == 100

    def test_save_report_with_nested_directories(self, tmp_path):
        """Test saving report in nested directories."""
        report = {'test': 'value'}
        nested_path = tmp_path / "reports" / "json" / "report.json"
        result_path = save_validation_report(report, str(nested_path))

        assert os.path.exists(result_path)