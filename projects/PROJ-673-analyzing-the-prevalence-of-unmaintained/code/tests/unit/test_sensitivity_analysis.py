import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from src.analysis.sensitivity_analysis import (
    calculate_unmaintained_proportion,
    run_sensitivity_analysis
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'package_name': ['pkg1', 'pkg2', 'pkg3', 'pkg4', 'pkg5'],
        'age_in_days': [100, 200, 400, None, 50],
        'vulnerability_count': [1, 2, 0, 3, 0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_output_path():
    """Create a temporary path for output JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, 'sensitivity_test.json')

class TestCalculateUnmaintainedProportion:
    def test_basic_proportion_calculation(self, sample_dataframe):
        """Test proportion calculation with 90-day threshold."""
        # 3 out of 4 valid rows are >= 90 days (100, 200, 400)
        # None is excluded
        result = calculate_unmaintained_proportion(sample_dataframe, 90)
        assert result == 0.75  # 3/4

    def test_high_threshold(self, sample_dataframe):
        """Test with threshold higher than most ages."""
        # Only 400 >= 365, so 1 out of 4
        result = calculate_unmaintained_proportion(sample_dataframe, 365)
        assert result == 0.25

    def test_low_threshold(self, sample_dataframe):
        """Test with threshold lower than all ages."""
        # All 4 valid rows >= 10
        result = calculate_unmaintained_proportion(sample_dataframe, 10)
        assert result == 1.0

    def test_all_null(self):
        """Test when all age_in_days are null."""
        df = pd.DataFrame({
            'package_name': ['pkg1', 'pkg2'],
            'age_in_days': [None, None],
            'vulnerability_count': [1, 2]
        })
        result = calculate_unmaintained_proportion(df, 90)
        assert result == 0.0

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame(columns=['package_name', 'age_in_days', 'vulnerability_count'])
        result = calculate_unmaintained_proportion(df, 90)
        assert result == 0.0

class TestRunSensitivityAnalysis:
    def test_full_pipeline(self, temp_csv_path, temp_output_path):
        """Test the full sensitivity analysis pipeline."""
        results = run_sensitivity_analysis(temp_csv_path, temp_output_path)
        
        # Check structure
        assert 'thresholds_tested' in results
        assert 'total_samples' in results
        assert 'valid_samples' in results
        assert 'results' in results
        
        # Check values
        assert results['total_samples'] == 5
        assert results['valid_samples'] == 4
        assert len(results['results']) == 3  # 3 thresholds
        
        # Check individual results
        for res in results['results']:
            assert 'threshold_days' in res
            assert 'proportion_unmaintained' in res
            assert 'count_unmaintained' in res
            assert isinstance(res['proportion_unmaintained'], float)
            assert 0.0 <= res['proportion_unmaintained'] <= 1.0

    def test_output_file_created(self, temp_csv_path, temp_output_path):
        """Verify that the output JSON file is created."""
        run_sensitivity_analysis(temp_csv_path, temp_output_path)
        assert os.path.exists(temp_output_path)
        
        with open(temp_output_path, 'r') as f:
            data = json.load(f)
        assert 'results' in data

    def test_thresholds_in_output(self, temp_csv_path, temp_output_path):
        """Verify that tested thresholds are recorded."""
        custom_thresholds = [60, 120, 240]
        results = run_sensitivity_analysis(
            temp_csv_path, 
            temp_output_path, 
            thresholds=custom_thresholds
        )
        assert results['thresholds_tested'] == custom_thresholds

    def test_missing_release_handling(self, temp_csv_path, temp_output_path):
        """Verify that null age_in_days are handled correctly."""
        results = run_sensitivity_analysis(temp_csv_path, temp_output_path)
        
        # Total samples includes nulls, valid_samples excludes them
        assert results['total_samples'] > results['valid_samples']
        
        # Proportions should be calculated only on valid samples
        for res in results['results']:
            # count_unmaintained should be <= valid_samples
            assert res['count_unmaintained'] <= results['valid_samples']

class TestEdgeCases:
    def test_single_valid_sample(self, temp_output_path):
        """Test with only one valid age_in_days."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame({
                'package_name': ['pkg1', 'pkg2'],
                'age_in_days': [100, None],
                'vulnerability_count': [1, 2]
            }).to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            results = run_sensitivity_analysis(temp_path, temp_output_path)
            assert results['valid_samples'] == 1
            # With 1 sample, proportion is either 0.0 or 1.0
            for res in results['results']:
                assert res['proportion_unmaintained'] in [0.0, 1.0]
        finally:
            os.unlink(temp_path)

    def test_no_valid_samples(self, temp_output_path):
        """Test when no valid age_in_days exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame({
                'package_name': ['pkg1', 'pkg2'],
                'age_in_days': [None, None],
                'vulnerability_count': [1, 2]
            }).to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            results = run_sensitivity_analysis(temp_path, temp_output_path)
            assert results['valid_samples'] == 0
            assert results['total_samples'] == 2
            # All proportions should be 0.0
            for res in results['results']:
                assert res['proportion_unmaintained'] == 0.0
        finally:
            os.unlink(temp_path)
