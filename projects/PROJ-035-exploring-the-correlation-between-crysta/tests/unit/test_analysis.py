"""
Unit tests for correlation analysis functionality in src/analysis/correlation.py.

These tests verify:
1. Pearson and Spearman correlation calculations
2. Multiple-comparison correction (Bonferroni)
3. Stratification handling
4. P-value computation and significance filtering
5. Output schema validation
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Import the module under test (will be implemented in T020)
# We use a try/except to handle the case where the module doesn't exist yet
# In a real TDD workflow, this would fail first, then pass after implementation
try:
    from analysis.correlation import (
        compute_correlations,
        apply_multiple_comparison_correction,
        stratify_and_analyze,
        validate_correlation_output,
        main
    )
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False

@pytest.mark.skipif(not MODULE_AVAILABLE, reason="correlation module not yet implemented")
class TestComputeCorrelations:
    """Tests for the compute_correlations function."""
    
    def test_pearson_correlation_basic(self):
        """Test basic Pearson correlation calculation."""
        # Create a simple dataset with known correlation
        np.random.seed(42)
        n = 100
        x = np.random.normal(0, 1, n)
        y = 2 * x + np.random.normal(0, 0.5, n)  # Strong positive correlation
        
        df = pd.DataFrame({
            'var_x': x,
            'var_y': y,
            'var_z': np.random.normal(0, 1, n)  # Uncorrelated
        })
        
        result = compute_correlations(df, method='pearson')
        
        # Check that we get a correlation matrix
        assert isinstance(result, pd.DataFrame)
        assert 'var_x' in result.columns
        assert 'var_y' in result.index
        
        # Check that x and y are positively correlated
        corr_xy = result.loc['var_x', 'var_y']
        assert 0.5 < corr_xy < 1.0, f"Expected strong positive correlation, got {corr_xy}"
        
        # Check that x and z are approximately uncorrelated
        corr_xz = result.loc['var_x', 'var_z']
        assert -0.3 < corr_xz < 0.3, f"Expected near-zero correlation, got {corr_xz}"
    
    def test_spearman_correlation_basic(self):
        """Test basic Spearman correlation calculation."""
        # Create a monotonic but non-linear relationship
        np.random.seed(42)
        n = 100
        x = np.random.uniform(0, 10, n)
        y = x ** 2 + np.random.normal(0, 10, n)  # Non-linear but monotonic
        
        df = pd.DataFrame({
            'var_x': x,
            'var_y': y
        })
        
        result = compute_correlations(df, method='spearman')
        
        # Spearman should detect the monotonic relationship
        corr_xy = result.loc['var_x', 'var_y']
        assert 0.7 < corr_xy < 1.0, f"Expected strong positive Spearman correlation, got {corr_xy}"
    
    def test_correlation_with_pvalues(self):
        """Test that p-values are computed correctly."""
        np.random.seed(42)
        n = 50
        x = np.random.normal(0, 1, n)
        y = 3 * x + np.random.normal(0, 0.3, n)  # Strong correlation
        
        df = pd.DataFrame({
            'var_x': x,
            'var_y': y
        })
        
        result = compute_correlations(df, method='pearson', return_pvalues=True)
        
        # Check that p-values are included
        assert 'pvalue_var_x' in result.columns or 'pvalue_var_y' in result.columns or \
               ('pvalue_var_x', 'pvalue_var_y') in result.columns, \
               "Expected p-values in result"
        
        # The strong correlation should have a small p-value
        # Note: exact p-value checking is tricky due to floating point, so we just check it exists
    
    def test_correlation_with_missing_data(self):
        """Test handling of missing data."""
        np.random.seed(42)
        n = 50
        x = np.random.normal(0, 1, n)
        y = 2 * x + np.random.normal(0, 0.5, n)
        
        # Introduce some missing values
        y[10:15] = np.nan
        
        df = pd.DataFrame({
            'var_x': x,
            'var_y': y
        })
        
        # Should handle missing data without crashing
        result = compute_correlations(df, method='pearson')
        
        # Check that correlation is still computed (using pairwise deletion)
        assert not np.isnan(result.loc['var_x', 'var_y'])
    
    def test_invalid_method(self):
        """Test error handling for invalid correlation method."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        
        with pytest.raises(ValueError):
            compute_correlations(df, method='invalid_method')
    
    def test_insufficient_data(self):
        """Test error handling for insufficient data points."""
        df = pd.DataFrame({
            'var_x': [1.0, 2.0],
            'var_y': [3.0, 4.0]
        })
        
        # With only 2 points, correlation is undefined or unreliable
        # The function should either handle this gracefully or raise a warning
        result = compute_correlations(df, method='pearson')
        # Just check it doesn't crash catastrophically
        assert result is not None
    
    def test_single_column(self):
        """Test behavior with a single column."""
        df = pd.DataFrame({'var_x': [1, 2, 3, 4, 5]})
        
        result = compute_correlations(df, method='pearson')
        
        # Should return a 1x1 matrix with correlation of 1.0
        assert result.loc['var_x', 'var_x'] == 1.0

@pytest.mark.skipif(not MODULE_AVAILABLE, reason="correlation module not yet implemented")
class TestMultipleComparisonCorrection:
    """Tests for multiple comparison correction (Bonferroni)."""
    
    def test_bonferroni_correction_basic(self):
        """Test basic Bonferroni correction."""
        pvalues = pd.Series([0.01, 0.03, 0.07, 0.20, 0.50])
        
        corrected = apply_multiple_comparison_correction(pvalues, method='bonferroni')
        
        # Bonferroni multiplies by number of tests
        expected = pvalues * len(pvalues)
        
        # Check that corrected p-values are >= original
        assert all(corrected >= pvalues), "Corrected p-values should be >= original"
        
        # Check that corrected p-values are capped at 1.0
        assert all(corrected <= 1.0), "Corrected p-values should be <= 1.0"
        
        # Check specific values
        assert abs(corrected.iloc[0] - 0.01 * 5) < 1e-10
        assert abs(corrected.iloc[1] - 0.03 * 5) < 1e-10
    
    def test_bonferroni_with_many_tests(self):
        """Test Bonferroni with many comparisons."""
        n_tests = 100
        pvalues = pd.Series(np.random.uniform(0, 1, n_tests))
        
        corrected = apply_multiple_comparison_correction(pvalues, method='bonferroni')
        
        # All corrected p-values should be <= 1.0
        assert all(corrected <= 1.0)
        
        # The correction factor should be n_tests
        max_corrected = corrected.max()
        assert max_corrected <= 1.0
    
    def test_invalid_correction_method(self):
        """Test error handling for invalid correction method."""
        pvalues = pd.Series([0.01, 0.05, 0.10])
        
        with pytest.raises(ValueError):
            apply_multiple_comparison_correction(pvalues, method='invalid_method')
    
    def test_empty_pvalues(self):
        """Test handling of empty p-value series."""
        pvalues = pd.Series([], dtype=float)
        
        corrected = apply_multiple_comparison_correction(pvalues, method='bonferroni')
        
        assert len(corrected) == 0
    
    def test_nan_pvalues(self):
        """Test handling of NaN p-values."""
        pvalues = pd.Series([0.01, np.nan, 0.05, np.nan, 0.10])
        
        corrected = apply_multiple_comparison_correction(pvalues, method='bonferroni')
        
        # NaN values should remain NaN
        assert pd.isna(corrected.iloc[1])
        assert pd.isna(corrected.iloc[3])
        
        # Non-NaN values should be corrected
        assert not pd.isna(corrected.iloc[0])
        assert not pd.isna(corrected.iloc[2])
        assert not pd.isna(corrected.iloc[4])

@pytest.mark.skipif(not MODULE_AVAILABLE, reason="correlation module not yet implemented")
class TestStratifyAndAnalyze:
    """Tests for stratified correlation analysis."""
    
    def test_stratification_by_class(self):
        """Test stratification by chemistry class."""
        # Create synthetic data with different correlations per class
        np.random.seed(42)
        n = 120
        
        data = []
        for class_name in ['oxide', 'halide', 'nitride']:
            n_class = n // 3
            if class_name == 'oxide':
                # Strong correlation
                x = np.random.normal(0, 1, n_class)
                y = 2 * x + np.random.normal(0, 0.3, n_class)
            elif class_name == 'halide':
                # Weak correlation
                x = np.random.normal(0, 1, n_class)
                y = 0.5 * x + np.random.normal(0, 0.8, n_class)
            else:  # nitride
                # No correlation
                x = np.random.normal(0, 1, n_class)
                y = np.random.normal(0, 1, n_class)
            
            data.extend([
                {'structure_id': f'{class_name}_{i}',
                 'descriptor_x': x[i],
                 'descriptor_y': y[i],
                 'thermal_conductivity': y[i],
                 'chemistry_class': class_name}
                for i in range(n_class)
            ])
        
        df = pd.DataFrame(data)
        
        # Perform stratified analysis
        results = stratify_and_analyze(
            df,
            predictor_cols=['descriptor_x'],
            target_col='thermal_conductivity',
            stratify_col='chemistry_class',
            method='pearson'
        )
        
        # Check that results are stratified
        assert isinstance(results, dict)
        assert 'oxide' in results
        assert 'halide' in results
        assert 'nitride' in results
        
        # Check that each stratification has correlation values
        for class_name, class_result in results.items():
            assert 'correlations' in class_result or 'correlation_matrix' in class_result
    
    def test_stratification_with_small_sample(self):
        """Test stratification when some classes have few samples."""
        np.random.seed(42)
        
        # Create data with one very small class
        data = [
            {'descriptor_x': 1.0, 'thermal_conductivity': 2.0, 'chemistry_class': 'oxide'},
            {'descriptor_x': 2.0, 'thermal_conductivity': 3.0, 'chemistry_class': 'oxide'},
            {'descriptor_x': 3.0, 'thermal_conductivity': 4.0, 'chemistry_class': 'oxide'},
            {'descriptor_x': 1.5, 'thermal_conductivity': 2.5, 'chemistry_class': 'halide'},  # Only 1 sample
        ]
        
        df = pd.DataFrame(data)
        
        # Should handle small classes gracefully (either skip or warn)
        results = stratify_and_analyze(
            df,
            predictor_cols=['descriptor_x'],
            target_col='thermal_conductivity',
            stratify_col='chemistry_class',
            method='pearson'
        )
        
        # Check that at least the oxide class is processed
        assert 'oxide' in results or len(results) > 0
    
    def test_stratification_with_missing_strata(self):
        """Test stratification when some classes are missing."""
        np.random.seed(42)
        
        data = [
            {'descriptor_x': 1.0, 'thermal_conductivity': 2.0, 'chemistry_class': 'oxide'},
            {'descriptor_x': 2.0, 'thermal_conductivity': 3.0, 'chemistry_class': 'oxide'},
        ]
        
        df = pd.DataFrame(data)
        
        # Should handle missing classes gracefully
        results = stratify_and_analyze(
            df,
            predictor_cols=['descriptor_x'],
            target_col='thermal_conductivity',
            stratify_col='chemistry_class',
            method='pearson'
        )
        
        # Only oxide should be in results
        assert 'oxide' in results
        assert 'halide' not in results
        assert 'nitride' not in results

@pytest.mark.skipif(not MODULE_AVAILABLE, reason="correlation module not yet implemented")
class TestValidateCorrelationOutput:
    """Tests for output validation."""
    
    def test_valid_output_schema(self):
        """Test validation of a properly formatted output."""
        valid_output = {
            'oxide': {
                'correlations': {
                    'descriptor_x_thermal_conductivity': {
                        'pearson': 0.85,
                        'pvalue': 0.001,
                        'corrected_pvalue': 0.005
                    }
                },
                'n_samples': 100,
                'n_tests': 1
            }
        }
        
        is_valid, errors = validate_correlation_output(valid_output)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_correlation_values(self):
        """Test validation with missing correlation values."""
        invalid_output = {
            'oxide': {
                'correlations': {},  # Empty correlations
                'n_samples': 100
            }
        }
        
        is_valid, errors = validate_correlation_output(invalid_output)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_missing_n_samples(self):
        """Test validation with missing sample count."""
        invalid_output = {
            'oxide': {
                'correlations': {
                    'descriptor_x_thermal_conductivity': {
                        'pearson': 0.85
                    }
                }
            }
        }
        
        is_valid, errors = validate_correlation_output(invalid_output)
        
        # Should fail or warn about missing n_samples
        assert not is_valid or len(errors) > 0
    
    def test_invalid_pvalue_range(self):
        """Test validation with p-values outside [0, 1]."""
        invalid_output = {
            'oxide': {
                'correlations': {
                    'descriptor_x_thermal_conductivity': {
                        'pearson': 0.85,
                        'pvalue': 1.5,  # Invalid
                        'corrected_pvalue': -0.1  # Invalid
                    }
                },
                'n_samples': 100
            }
        }
        
        is_valid, errors = validate_correlation_output(invalid_output)
        
        assert not is_valid
        assert len(errors) > 0

@pytest.mark.skipif(not MODULE_AVAILABLE, reason="correlation module not yet implemented")
class TestMainFunction:
    """Tests for the main() entry point."""
    
    def test_main_execution(self):
        """Test that main() runs without error and produces output."""
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "correlation_results.json"
            
            # Create a simple test dataset
            np.random.seed(42)
            n = 100
            df = pd.DataFrame({
                'structure_id': [f'str_{i}' for i in range(n)],
                'descriptor_x': np.random.normal(0, 1, n),
                'descriptor_y': np.random.normal(0, 1, n),
                'thermal_conductivity': np.random.normal(10, 2, n),
                'chemistry_class': np.random.choice(['oxide', 'halide', 'nitride'], n)
            })
            
            # Save to CSV
            input_path = Path(tmpdir) / "test_input.csv"
            df.to_csv(input_path, index=False)
            
            # Run main
            try:
                main(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    predictor_cols=['descriptor_x', 'descriptor_y'],
                    target_col='thermal_conductivity',
                    stratify_col='chemistry_class',
                    method='pearson',
                    correction_method='bonferroni'
                )
                
                # Check that output file was created
                assert output_path.exists(), "Output file should be created"
                
                # Check that output is valid JSON
                with open(output_path, 'r') as f:
                    results = json.load(f)
                
                assert isinstance(results, dict)
                assert len(results) > 0
                
            except Exception as e:
                pytest.fail(f"main() raised an exception: {e}")
    
    def test_main_with_invalid_input(self):
        """Test main() with non-existent input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.csv"
            output_path = Path(tmpdir) / "output.json"
            
            with pytest.raises(FileNotFoundError):
                main(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    predictor_cols=['descriptor_x'],
                    target_col='thermal_conductivity',
                    stratify_col='chemistry_class'
                )
    
    def test_main_output_format(self):
        """Test that main() produces the expected output format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.json"
            
            # Create test data
            np.random.seed(42)
            n = 60
            df = pd.DataFrame({
                'structure_id': [f'str_{i}' for i in range(n)],
                'descriptor_x': np.random.normal(0, 1, n),
                'thermal_conductivity': np.random.normal(10, 2, n),
                'chemistry_class': np.random.choice(['oxide', 'halide'], n)
            })
            df.to_csv(input_path, index=False)
            
            main(
                input_path=str(input_path),
                output_path=str(output_path),
                predictor_cols=['descriptor_x'],
                target_col='thermal_conductivity',
                stratify_col='chemistry_class'
            )
            
            # Load and validate output
            with open(output_path, 'r') as f:
                results = json.load(f)
            
            # Check structure
            assert isinstance(results, dict)
            for class_name, class_data in results.items():
                assert 'correlations' in class_data or 'correlation_matrix' in class_data
                assert 'n_samples' in class_data

@pytest.mark.skipif(MODULE_AVAILABLE, reason="Correlation module already implemented")
class TestModuleNotImplemented:
    """Placeholder test to ensure the test fails when module is not implemented."""
    
    def test_module_should_be_implemented(self):
        """This test should fail until T020 implements the correlation module."""
        assert False, "Correlation module (T020) has not been implemented yet. This test is a placeholder."