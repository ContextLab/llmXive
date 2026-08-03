"""
Unit tests for the correlation analysis module (T021).
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
from scipy.stats import spearmanr
from src.analysis.correlation import (
    load_dependencies_data,
    calculate_spearman_correlation,
    run_correlation_analysis
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with age and vulnerability data."""
    return pd.DataFrame({
        'age_in_days': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'vulnerability_count': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'package_name': [f'pkg_{i}' for i in range(10)]
    })

@pytest.fixture
def temp_csv_path(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f.name, index=False)
        return f.name

@pytest.fixture
def temp_output_path():
    """Create a temporary path for output JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        return f.name

class TestLoadDependenciesData:
    def test_load_valid_csv(self, temp_csv_path):
        """Test loading a valid CSV file."""
        df = load_dependencies_data(temp_csv_path)
        assert len(df) == 10
        assert 'age_in_days' in df.columns
        assert 'vulnerability_count' in df.columns

    def test_load_csv_with_null_age(self):
        """Test that rows with null age_in_days are dropped."""
        df_input = pd.DataFrame({
            'age_in_days': [10, np.nan, 30, np.nan, 50],
            'vulnerability_count': [0, 1, 2, 3, 4]
        })
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_input.to_csv(f.name, index=False)
            temp_path = f.name
        
        df = load_dependencies_data(temp_path)
        assert len(df) == 3
        assert not df['age_in_days'].isna().any()

    def test_missing_file_raises_error(self):
        """Test that a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_dependencies_data('non_existent_file.csv')

    def test_missing_columns_raises_error(self):
        """Test that missing required columns raise ValueError."""
        df_input = pd.DataFrame({
            'age_in_days': [10, 20, 30],
            'other_column': [1, 2, 3]
        })
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_input.to_csv(f.name, index=False)
            temp_path = f.name
        
        with pytest.raises(ValueError):
            load_dependencies_data(temp_path)

class TestCalculateSpearmanCorrelation:
    def test_perfect_positive_correlation(self, sample_dataframe):
        """Test calculation with perfect positive correlation."""
        rho, p_value, stats = calculate_spearman_correlation(sample_dataframe)
        assert abs(rho - 1.0) < 1e-6
        assert p_value < 0.05  # Should be significant
        assert stats['n'] == 10

    def test_perfect_negative_correlation(self):
        """Test calculation with perfect negative correlation."""
        df = pd.DataFrame({
            'age_in_days': [10, 20, 30, 40, 50],
            'vulnerability_count': [5, 4, 3, 2, 1]
        })
        rho, p_value, stats = calculate_spearman_correlation(df)
        assert abs(rho - (-1.0)) < 1e-6
        assert p_value < 0.05

    def test_no_correlation(self):
        """Test calculation with no correlation."""
        df = pd.DataFrame({
            'age_in_days': [10, 20, 30, 40, 50],
            'vulnerability_count': [0, 5, 2, 4, 1]
        })
        rho, p_value, stats = calculate_spearman_correlation(df)
        assert -0.5 < rho < 0.5  # Weak correlation
        assert stats['n'] == 5

    def test_insufficient_data(self):
        """Test that insufficient data raises an error."""
        df = pd.DataFrame({
            'age_in_days': [10],
            'vulnerability_count': [1]
        })
        with pytest.raises(ValueError, match="Insufficient data points"):
            calculate_spearman_correlation(df)

    def test_constant_values(self):
        """Test handling of constant values in one variable."""
        df = pd.DataFrame({
            'age_in_days': [10, 10, 10, 10],
            'vulnerability_count': [1, 2, 3, 4]
        })
        rho, p_value, stats = calculate_spearman_correlation(df)
        assert np.isnan(rho)
        assert np.isnan(p_value)
        assert stats['n'] == 4

class TestRunCorrelationAnalysis:
    def test_full_pipeline(self, temp_csv_path, temp_output_path):
        """Test the full analysis pipeline."""
        result = run_correlation_analysis(temp_csv_path, temp_output_path)
        
        assert 'correlation_coefficient' in result
        assert 'p_value' in result
        assert 'is_significant' in result
        assert 'sample_size' in result
        assert 'statistics' in result
        
        assert -1 <= result['correlation_coefficient'] <= 1
        assert 0 <= result['p_value'] <= 1
        assert result['sample_size'] == 10

    def test_output_file_created(self, temp_csv_path, temp_output_path):
        """Test that output JSON file is created."""
        run_correlation_analysis(temp_csv_path, temp_output_path)
        
        assert Path(temp_output_path).exists()
        
        with open(temp_output_path, 'r') as f:
            saved_result = json.load(f)
        
        assert 'correlation_coefficient' in saved_result
        assert saved_result['correlation_coefficient'] == pytest.approx(1.0, abs=1e-6)

    def test_default_output_path(self, temp_csv_path):
        """Test that results can be returned without saving to file."""
        result = run_correlation_analysis(temp_csv_path)
        assert result['correlation_coefficient'] is not None

class TestEdgeCases:
    def test_large_vulnerability_counts(self):
        """Test with large vulnerability counts."""
        df = pd.DataFrame({
            'age_in_days': [10, 20, 30, 40, 50],
            'vulnerability_count': [100, 200, 300, 400, 500]
        })
        rho, p_value, stats = calculate_spearman_correlation(df)
        assert abs(rho - 1.0) < 1e-6

    def test_zero_vulnerabilities(self):
        """Test with all zero vulnerabilities."""
        df = pd.DataFrame({
            'age_in_days': [10, 20, 30, 40, 50],
            'vulnerability_count': [0, 0, 0, 0, 0]
        })
        rho, p_value, stats = calculate_spearman_correlation(df)
        assert np.isnan(rho)  # Constant zero values

    def test_mixed_null_handling(self):
        """Test handling of mixed null values."""
        df_input = pd.DataFrame({
            'age_in_days': [10, np.nan, 30, 40, np.nan],
            'vulnerability_count': [1, 2, np.nan, 4, 5]
        })
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_input.to_csv(f.name, index=False)
            temp_path = f.name
        
        df = load_dependencies_data(temp_path)
        # Only rows with both non-null values should remain
        assert len(df) == 2  # Rows 0 and 3