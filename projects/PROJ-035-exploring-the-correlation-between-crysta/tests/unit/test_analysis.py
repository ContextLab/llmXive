"""
Unit tests for correlation analysis functionality.

This module provides comprehensive unit tests for the correlation analysis
pipeline, including Pearson/Spearman correlation calculations, multiple
comparison corrections (Bonferroni and FDR), and stratified analysis by
chemistry class.

Tests are designed to fail first (TDD approach) before implementation.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from analysis.correlation import (
    compute_correlation_matrix,
    stratified_correlation_analysis,
    save_correlation_results
)

# Test fixtures and helper data

@pytest.fixture
def sample_data():
    """Create a sample dataset for correlation testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Generate correlated features
    x1 = np.random.normal(0, 1, n_samples)
    x2 = x1 * 0.8 + np.random.normal(0, 0.5, n_samples)  # Correlated with x1
    x3 = np.random.normal(0, 1, n_samples)  # Independent
    x4 = x3 * 0.6 + np.random.normal(0, 0.7, n_samples)  # Correlated with x3
    
    # Target variable with known relationships
    y = 2.5 * x1 + 1.2 * x3 + np.random.normal(0, 0.3, n_samples)
    
    # Create DataFrame with chemistry classes
    df = pd.DataFrame({
        'structure_id': [f'struct_{i}' for i in range(n_samples)],
        'thermal_conductivity': y,
        'tilting_angle': x1,
        'bond_length_variance': x2,
        'tolerance_factor': x3,
        'unit_cell_volume': x4,
        'chemistry_class': np.random.choice(['oxide', 'halide', 'nitride'], n_samples)
    })
    
    return df

@pytest.fixture
def small_dataset():
    """Create a small dataset for edge case testing."""
    np.random.seed(123)
    n_samples = 10
    
    df = pd.DataFrame({
        'structure_id': [f'struct_{i}' for i in range(n_samples)],
        'thermal_conductivity': np.random.normal(10, 2, n_samples),
        'tilting_angle': np.random.normal(0.05, 0.01, n_samples),
        'bond_length_variance': np.random.normal(0.02, 0.005, n_samples),
        'tolerance_factor': np.random.normal(0.98, 0.01, n_samples),
        'unit_cell_volume': np.random.normal(100, 10, n_samples),
        'chemistry_class': ['oxide'] * n_samples
    })
    
    return df

@pytest.fixture
def stratified_data():
    """Create data with distinct chemistry classes."""
    np.random.seed(456)
    
    oxide_data = pd.DataFrame({
        'structure_id': [f'oxide_{i}' for i in range(30)],
        'thermal_conductivity': np.random.normal(15, 3, 30),
        'tilting_angle': np.random.normal(0.04, 0.008, 30),
        'bond_length_variance': np.random.normal(0.015, 0.003, 30),
        'tolerance_factor': np.random.normal(0.99, 0.005, 30),
        'unit_cell_volume': np.random.normal(95, 8, 30),
        'chemistry_class': 'oxide'
    })
    
    halide_data = pd.DataFrame({
        'structure_id': [f'halide_{i}' for i in range(25)],
        'thermal_conductivity': np.random.normal(8, 2, 25),
        'tilting_angle': np.random.normal(0.06, 0.012, 25),
        'bond_length_variance': np.random.normal(0.025, 0.006, 25),
        'tolerance_factor': np.random.normal(0.96, 0.008, 25),
        'unit_cell_volume': np.random.normal(110, 12, 25),
        'chemistry_class': 'halide'
    })
    
    nitride_data = pd.DataFrame({
        'structure_id': [f'nitride_{i}' for i in range(20)],
        'thermal_conductivity': np.random.normal(25, 5, 20),
        'tilting_angle': np.random.normal(0.03, 0.006, 20),
        'bond_length_variance': np.random.normal(0.01, 0.002, 20),
        'tolerance_factor': np.random.normal(1.01, 0.004, 20),
        'unit_cell_volume': np.random.normal(85, 6, 20),
        'chemistry_class': 'nitride'
    })
    
    return pd.concat([oxide_data, halide_data, nitride_data], ignore_index=True)

# Test Pearson Correlation

class TestPearsonCorrelation:
    """Tests for Pearson correlation coefficient calculation."""
    
    def test_pearson_positive_correlation(self, sample_data):
        """Test that positively correlated variables yield positive r values."""
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(sample_data, predictors, target, method='pearson')
        
        # tilting_angle should be positively correlated with thermal_conductivity
        assert result['tilting_angle']['thermal_conductivity']['r'] > 0.5
        assert result['tilting_angle']['thermal_conductivity']['p_value'] < 0.05
    
    def test_pearson_negative_correlation(self, sample_data):
        """Test that negatively correlated variables yield negative r values."""
        # Create data with known negative correlation
        np.random.seed(789)
        df = pd.DataFrame({
            'x': np.random.normal(0, 1, 50),
            'y': -0.8 * np.random.normal(0, 1, 50) + 0.2 * np.random.normal(0, 1, 50)
        })
        
        result = compute_correlation_matrix(df, ['x'], 'y', method='pearson')
        
        assert result['x']['y']['r'] < 0
        assert result['x']['y']['p_value'] < 0.05
    
    def test_pearson_independent_variables(self, sample_data):
        """Test that independent variables yield near-zero correlation."""
        # x3 and x4 are correlated, but we test x3 vs an independent variable
        np.random.seed(999)
        df = pd.DataFrame({
            'x': np.random.normal(0, 1, 100),
            'y': np.random.normal(0, 1, 100)  # Independent
        })
        
        result = compute_correlation_matrix(df, ['x'], 'y', method='pearson')
        
        # Correlation should be close to zero (within random variation)
        assert abs(result['x']['y']['r']) < 0.3
    
    def test_pearson_p_value_significance(self, sample_data):
        """Test that p-values are correctly calculated for significant correlations."""
        predictors = ['tilting_angle', 'tolerance_factor']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(sample_data, predictors, target, method='pearson')
        
        # Both should be significant given our synthetic data construction
        assert result['tilting_angle']['thermal_conductivity']['p_value'] < 0.05
        assert result['tolerance_factor']['thermal_conductivity']['p_value'] < 0.05

# Test Spearman Correlation

class TestSpearmanCorrelation:
    """Tests for Spearman rank correlation coefficient calculation."""
    
    def test_spearmon_robust_to_outliers(self, sample_data):
        """Test that Spearman correlation is robust to outliers."""
        df = sample_data.copy()
        # Add extreme outliers
        df.loc[0, 'thermal_conductivity'] = 1000
        df.loc[1, 'thermal_conductivity'] = -500
        
        result = compute_correlation_matrix(df, ['tilting_angle'], 'thermal_conductivity', method='spearman')
        
        # Should still detect correlation despite outliers
        assert result['tilting_angle']['thermal_conductivity']['p_value'] < 0.05
    
    def test_spearman_monotonic_relationship(self, sample_data):
        """Test Spearman on a monotonic but non-linear relationship."""
        np.random.seed(555)
        x = np.linspace(0, 10, 50)
        y = x**2 + np.random.normal(0, 5, 50)  # Monotonic but non-linear
        
        df = pd.DataFrame({'x': x, 'y': y})
        result = compute_correlation_matrix(df, ['x'], 'y', method='spearman')
        
        # Should detect strong monotonic relationship
        assert result['x']['y']['r'] > 0.8
        assert result['x']['y']['p_value'] < 0.001

# Test Multiple Comparison Correction

class TestBenjaminiHochbergCorrection:
    """Tests for False Discovery Rate (FDR) correction."""
    
    def test_fdr_correction_reduces_p_values(self, sample_data):
        """Test that FDR correction adjusts p-values appropriately."""
        predictors = ['tilting_angle', 'bond_length_variance', 'tolerance_factor', 'unit_cell_volume']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(sample_data, predictors, target, method='pearson', correction_method='fdr')
        
        # All results should have corrected p-values
        for predictor in predictors:
            assert 'corrected_p_value' in result[predictor][target]
            # Corrected p-value should be >= original p-value
            assert result[predictor][target]['corrected_p_value'] >= result[predictor][target]['p_value']
    
    def test_bonferroni_correction(self, sample_data):
        """Test Bonferroni correction implementation."""
        predictors = ['tilting_angle', 'bond_length_variance', 'tolerance_factor']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(
            sample_data, predictors, target, 
            method='pearson', 
            correction_method='bonferroni'
        )
        
        for predictor in predictors:
            assert 'corrected_p_value' in result[predictor][target]
            # Bonferroni is more conservative than FDR
            assert result[predictor][target]['corrected_p_value'] >= result[predictor][target]['p_value']
    
    def test_no_correction_option(self, sample_data):
        """Test that no correction returns original p-values."""
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(
            sample_data, predictors, target, 
            method='pearson', 
            correction_method=None
        )
        
        for predictor in predictors:
            # Without correction, corrected_p_value should equal p_value
            assert result[predictor][target]['corrected_p_value'] == result[predictor][target]['p_value']

# Test Correlation Matrix Structure

class TestCorrelationMatrix:
    """Tests for correlation matrix structure and completeness."""
    
    def test_matrix_structure(self, sample_data):
        """Test that correlation matrix has correct structure."""
        predictors = ['tilting_angle', 'bond_length_variance', 'tolerance_factor']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(sample_data, predictors, target, method='pearson')
        
        # Check structure
        assert isinstance(result, dict)
        assert len(result) == len(predictors)
        
        for predictor in predictors:
            assert predictor in result
            assert target in result[predictor]
            assert 'r' in result[predictor][target]
            assert 'p_value' in result[predictor][target]
            assert 'n_samples' in result[predictor][target]
    
    def test_all_predictors_included(self, sample_data):
        """Test that all requested predictors are included in results."""
        predictors = ['tilting_angle', 'bond_length_variance', 'tolerance_factor', 'unit_cell_volume']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(sample_data, predictors, target, method='pearson')
        
        assert set(result.keys()) == set(predictors)
    
    def test_n_samples_tracking(self, sample_data):
        """Test that number of samples is correctly tracked."""
        predictors = ['tilting_angle']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(sample_data, predictors, target, method='pearson')
        
        assert result['tilting_angle']['thermal_conductivity']['n_samples'] == len(sample_data)

# Test Stratified Analysis

class TestStratifiedAnalysis:
    """Tests for stratified correlation analysis by chemistry class."""
    
    def test_stratification_by_chemistry_class(self, stratified_data):
        """Test that stratified analysis produces separate results for each class."""
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        result = stratified_correlation_analysis(
            stratified_data, 
            predictors, 
            target, 
            method='pearson',
            stratification_column='chemistry_class'
        )
        
        # Check that all chemistry classes are present
        assert 'oxide' in result['stratified_results']
        assert 'halide' in result['stratified_results']
        assert 'nitride' in result['stratified_results']
        
        # Each class should have results for all predictors
        for class_name, class_results in result['stratified_results'].items():
            for predictor in predictors:
                assert predictor in class_results
                assert target in class_results[predictor]
    
    def test_stratified_sample_sizes(self, stratified_data):
        """Test that stratified analysis correctly reports sample sizes."""
        predictors = ['tilting_angle']
        target = 'thermal_conductivity'
        
        result = stratified_correlation_analysis(
            stratified_data, 
            predictors, 
            target, 
            method='pearson',
            stratification_column='chemistry_class'
        )
        
        # Check sample sizes match expected counts
        assert result['stratified_results']['oxide']['tilting_angle']['thermal_conductivity']['n_samples'] == 30
        assert result['stratified_results']['halide']['tilting_angle']['thermal_conductivity']['n_samples'] == 25
        assert result['stratified_results']['nitride']['tilting_angle']['thermal_conductivity']['n_samples'] == 20
    
    def test_stratified_with_correction(self, stratified_data):
        """Test stratified analysis with multiple comparison correction."""
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        result = stratified_correlation_analysis(
            stratified_data, 
            predictors, 
            target, 
            method='pearson',
            stratification_column='chemistry_class',
            correction_method='fdr'
        )
        
        # Check that corrected p-values are present in all strata
        for class_name, class_results in result['stratified_results'].items():
            for predictor in predictors:
                assert 'corrected_p_value' in class_results[predictor][target]
    
    def test_stratified_empty_class_handling(self, sample_data):
        """Test handling of classes with insufficient samples."""
        # Create data with one class having very few samples
        df = sample_data.copy()
        df.loc[0:2, 'chemistry_class'] = 'rare_class'
        
        predictors = ['tilting_angle']
        target = 'thermal_conductivity'
        
        # Should not raise an error, but may warn or skip
        result = stratified_correlation_analysis(
            df, 
            predictors, 
            target, 
            method='pearson',
            stratification_column='chemistry_class'
        )
        
        # The rare class should either be excluded or have NaN results
        if 'rare_class' in result['stratified_results']:
            # If included, it should have valid structure
            assert 'tilting_angle' in result['stratified_results']['rare_class']

# Test Result Saving

class TestSaveCorrelationResults:
    """Tests for correlation result serialization."""
    
    def test_save_to_json(self, sample_data, tmp_path):
        """Test saving correlation results to JSON file."""
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        results = compute_correlation_matrix(sample_data, predictors, target, method='pearson')
        
        output_file = tmp_path / "correlation_results.json"
        save_correlation_results(results, str(output_file))
        
        # Check file exists
        assert output_file.exists()
        
        # Check file is valid JSON
        import json
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert 'tilting_angle' in loaded
        assert 'bond_length_variance' in loaded

# Edge Cases

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_constant_variable(self, small_dataset):
        """Test handling of constant variables (zero variance)."""
        df = small_dataset.copy()
        df['constant_var'] = 5.0  # Constant value
        
        predictors = ['constant_var', 'tilting_angle']
        target = 'thermal_conductivity'
        
        # Should handle constant variable gracefully
        result = compute_correlation_matrix(df, predictors, target, method='pearson')
        
        # Constant variable should have NaN or 0 correlation
        corr_val = result['constant_var']['thermal_conductivity']['r']
        assert np.isnan(corr_val) or corr_val == 0
    
    def test_insufficient_samples(self, small_dataset):
        """Test behavior with very small sample size."""
        df = small_dataset.copy()
        
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        # Should still compute (though with low power)
        result = compute_correlation_matrix(df, predictors, target, method='pearson')
        
        assert len(result) == len(predictors)
    
    def test_missing_values(self, sample_data):
        """Test handling of missing values."""
        df = sample_data.copy()
        df.loc[0:5, 'tilting_angle'] = np.nan
        
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        # Should handle missing values (pairwise deletion)
        result = compute_correlation_matrix(df, predictors, target, method='pearson')
        
        # n_samples should be reduced for tilting_angle
        assert result['tilting_angle']['thermal_conductivity']['n_samples'] < len(df)
        # n_samples should be full for bond_length_variance
        assert result['bond_length_variance']['thermal_conductivity']['n_samples'] == len(df)
    
    def test_single_predictor(self, sample_data):
        """Test with single predictor."""
        predictors = ['tilting_angle']
        target = 'thermal_conductivity'
        
        result = compute_correlation_matrix(sample_data, predictors, target, method='pearson')
        
        assert len(result) == 1
        assert 'tilting_angle' in result

# Integration Tests

class TestCorrelationIntegration:
    """Integration tests for the full correlation pipeline."""
    
    def test_full_pipeline_pearson(self, sample_data):
        """Test complete Pearson correlation pipeline."""
        predictors = ['tilting_angle', 'bond_length_variance', 'tolerance_factor', 'unit_cell_volume']
        target = 'thermal_conductivity'
        
        # Compute correlations
        results = compute_correlation_matrix(
            sample_data, 
            predictors, 
            target, 
            method='pearson',
            correction_method='bonferroni'
        )
        
        # Verify all expected fields
        for predictor in predictors:
            assert predictor in results
            assert target in results[predictor]
            assert 'r' in results[predictor][target]
            assert 'p_value' in results[predictor][target]
            assert 'corrected_p_value' in results[predictor][target]
            assert 'n_samples' in results[predictor][target]
    
    def test_full_pipeline_spearman_stratified(self, stratified_data):
        """Test complete Spearman correlation pipeline with stratification."""
        predictors = ['tilting_angle', 'bond_length_variance']
        target = 'thermal_conductivity'
        
        results = stratified_correlation_analysis(
            stratified_data,
            predictors,
            target,
            method='spearman',
            stratification_column='chemistry_class',
            correction_method='fdr'
        )
        
        # Verify structure
        assert 'stratified_results' in results
        assert 'corrected_p_values' in results
        
        # Verify all classes present
        for class_name in ['oxide', 'halide', 'nitride']:
            assert class_name in results['stratified_results']
            for predictor in predictors:
                assert predictor in results['stratified_results'][class_name]
                assert target in results['stratified_results'][class_name][predictor]
                assert 'corrected_p_value' in results['stratified_results'][class_name][predictor][target]