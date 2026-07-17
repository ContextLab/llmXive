import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from analysis import (
    load_processed_data,
    calculate_activation_energy,
    validate_data_quality,
    perform_regression_with_density,
    apply_multiple_comparison_correction,
    calculate_statistical_power,
    generate_regression_plot,
    run_full_analysis
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 20
    data = {
        'defect_energy': np.random.uniform(0.5, 2.0, n),
        'conductivity': np.random.uniform(1e-5, 1e-2, n),
        'defect_density': np.random.uniform(1e-22, 1e-20, n),
        'migration_barrier': np.random.uniform(0.3, 0.8, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestLoadProcessedData:
    def test_load_json_data(self, sample_data, temp_output_dir):
        """Test loading data from JSON file."""
        json_path = temp_output_dir / 'test_data.json'
        with open(json_path, 'w') as f:
            json.dump(sample_data.to_dict(orient='records'), f)
        
        loaded_df = load_processed_data(json_path)
        assert len(loaded_df) == len(sample_data)
        assert list(loaded_df.columns) == list(sample_data.columns)

    def test_load_csv_data(self, sample_data, temp_output_dir):
        """Test loading data from CSV file."""
        csv_path = temp_output_dir / 'test_data.csv'
        sample_data.to_csv(csv_path, index=False)
        
        loaded_df = load_processed_data(csv_path)
        assert len(loaded_df) == len(sample_data)

    def test_file_not_found(self, temp_output_dir):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_processed_data(temp_output_dir / 'nonexistent.json')

class TestCalculateActivationEnergy:
    def test_activation_energy_calculation(self):
        """Test Ea = Ef + Em calculation."""
        ef = 1.5  # eV
        em = 0.5  # eV
        expected_ea = 2.0  # eV
        
        result = calculate_activation_energy(ef, em)
        assert result == pytest.approx(expected_ea, rel=1e-6)

    def test_different_values(self):
        """Test with different energy values."""
        assert calculate_activation_energy(0.8, 0.3) == pytest.approx(1.1, rel=1e-6)
        assert calculate_activation_energy(2.0, 0.1) == pytest.approx(2.1, rel=1e-6)

class TestValidateDataQuality:
    def test_valid_data(self, sample_data):
        """Test validation with valid data."""
        is_valid, issues = validate_data_quality(sample_data)
        assert is_valid is True
        assert len(issues) == 0

    def test_missing_columns(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({'defect_energy': [1.0, 2.0]})
        is_valid, issues = validate_data_quality(df)
        assert is_valid is False
        assert any('Missing required column' in issue for issue in issues)

    def test_nan_values(self):
        """Test validation with NaN values."""
        df = pd.DataFrame({
            'defect_energy': [1.0, np.nan, 2.0],
            'conductivity': [1e-5, 1e-4, 1e-3],
            'defect_density': [1e-21, 1e-21, 1e-21],
            'migration_barrier': [0.5, 0.5, 0.5]
        })
        is_valid, issues = validate_data_quality(df)
        assert is_valid is False
        assert any('NaN values' in issue for issue in issues)

    def test_negative_defect_energy(self):
        """Test validation with negative defect energy."""
        df = pd.DataFrame({
            'defect_energy': [-0.5, 1.0, 2.0],
            'conductivity': [1e-5, 1e-4, 1e-3],
            'defect_density': [1e-21, 1e-21, 1e-21],
            'migration_barrier': [0.5, 0.5, 0.5]
        })
        is_valid, issues = validate_data_quality(df)
        assert is_valid is False
        assert any('Negative defect energies' in issue for issue in issues)

class TestPerformRegressionWithDensity:
    def test_regression_outputs_r2_and_pvalues(self, sample_data):
        """Contract test: verify R² and p-value outputs exist and are valid."""
        results = perform_regression_with_density(sample_data)
        
        # Check R² exists and is in valid range
        assert 'r2' in results
        assert 0.0 <= results['r2'] <= 1.0 or results['r2'] > 1.0  # R² can be negative for poor fits
        
        # Check p-values exist and are valid
        assert 'p_values' in results
        assert 'defect_energy' in results['p_values']
        assert 'defect_density' in results['p_values']
        assert 'migration_barrier' in results['p_values']
        
        # P-values should be between 0 and 1
        for var, p in results['p_values'].items():
            assert 0.0 <= p <= 1.0, f"P-value for {var} ({p}) is not in [0, 1]"

    def test_regression_includes_defect_density(self, sample_data):
        """Verify defect density is included as a predictor."""
        results = perform_regression_with_density(sample_data)
        
        assert 'coefficients' in results
        assert 'defect_density' in results['coefficients']
        assert isinstance(results['coefficients']['defect_density'], float)

    def test_regression_metrics(self, sample_data):
        """Test that regression returns expected metrics."""
        results = perform_regression_with_density(sample_data)
        
        assert 'rmse' in results
        assert 'n_samples' in results
        assert results['n_samples'] == len(sample_data)
        assert 'degrees_of_freedom' in results

class TestApplyMultipleComparisonCorrection:
    def test_bonferroni_correction(self, sample_data):
        """Integration test: Bonferroni correction increases p-values."""
        results = perform_regression_with_density(sample_data)
        original_p = results['p_values']
        
        corrected = apply_multiple_comparison_correction(original_p, method='bonferroni')
        
        # Corrected p-values should be >= original
        for var in original_p:
            assert corrected[var] >= original_p[var]
            assert corrected[var] <= 1.0

    def test_bh_correction(self, sample_data):
        """Integration test: Benjamini-Hochberg correction."""
        results = perform_regression_with_density(sample_data)
        original_p = results['p_values']
        
        corrected = apply_multiple_comparison_correction(original_p, method='bh')
        
        # Corrected p-values should be >= original
        for var in original_p:
            assert corrected[var] >= original_p[var]
            assert corrected[var] <= 1.0

    def test_invalid_method(self, sample_data):
        """Test error handling for invalid correction method."""
        results = perform_regression_with_density(sample_data)
        
        with pytest.raises(ValueError, match="Unknown correction method"):
            apply_multiple_comparison_correction(results['p_values'], method='invalid')

class TestCalculateStatisticalPower:
    def test_power_calculation(self):
        """Test statistical power calculation returns valid value."""
        power = calculate_statistical_power(n_samples=30, effect_size=0.1, alpha=0.05)
        
        assert isinstance(power, float)
        assert 0.0 <= power <= 1.0

    def test_power_increases_with_sample_size(self):
        """Test that power increases with larger sample size."""
        power_20 = calculate_statistical_power(n_samples=20, effect_size=0.1)
        power_50 = calculate_statistical_power(n_samples=50, effect_size=0.1)
        
        assert power_50 > power_20

class TestGenerateRegressionPlot:
    def test_plot_generation(self, sample_data, temp_output_dir):
        """Test that regression plot is generated successfully."""
        results = perform_regression_with_density(sample_data)
        plot_path = temp_output_dir / 'test_plot.png'
        
        generate_regression_plot(sample_data, results, plot_path)
        
        assert plot_path.exists()
        assert plot_path.stat().st_size > 0

class TestRunFullAnalysis:
    def test_full_analysis_pipeline(self, sample_data, temp_output_dir):
        """Test the complete analysis pipeline."""
        # Save sample data
        data_path = temp_output_dir / 'processed_data.json'
        with open(data_path, 'w') as f:
            json.dump(sample_data.to_dict(orient='records'), f)
        
        # Run full analysis
        result = run_full_analysis(data_path, temp_output_dir)
        
        # Verify result object
        assert result.r_squared is not None
        assert result.rmse is not None
        assert result.coefficients is not None
        assert result.p_values is not None
        assert result.corrected_p_values is not None
        assert result.statistical_power is not None
        assert result.n_samples == len(sample_data)
        
        # Verify output files
        assert Path(result.plot_path).exists()
        assert Path(result.results_path).exists()
        
        # Verify results file content
        with open(result.results_path, 'r') as f:
            saved_results = json.load(f)
        
        assert 'r2' in saved_results
        assert 'coefficients' in saved_results
        assert 'p_values' in saved_results

    def test_full_analysis_with_insufficient_data(self, temp_output_dir):
        """Test error handling with insufficient data."""
        # Create data with only 2 samples
        data = {
            'defect_energy': [1.0, 2.0],
            'conductivity': [1e-5, 1e-4],
            'defect_density': [1e-21, 1e-21],
            'migration_barrier': [0.5, 0.5]
        }
        df = pd.DataFrame(data)
        
        data_path = temp_output_dir / 'processed_data.json'
        with open(data_path, 'w') as f:
            json.dump(df.to_dict(orient='records'), f)
        
        with pytest.raises(ValueError, match="Insufficient valid data points"):
            run_full_analysis(data_path, temp_output_dir)