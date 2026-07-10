"""
Unit tests for statistical test logic in code/analysis/statistical_test.py.

Tests cover:
1. Normality testing (Shapiro-Wilk) on residuals
2. Selection of Pearson vs Spearman correlation based on normality
3. Calculation of correlation coefficient and p-value
4. Significance flag determination
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import tempfile
import os

# Import the module under test
# Note: The task description references code/analysis/statistical_test.py
# but the file hasn't been created yet. We will create it as part of this task
# to ensure the tests have something to test.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import statistical_test

class TestStatisticalTest:
    """Unit tests for statistical analysis functions."""
    
    def test_shapiro_wilk_normal_residuals(self):
        """Test Shapiro-Wilk test on normally distributed residuals."""
        # Generate normally distributed residuals
        np.random.seed(42)
        residuals = np.random.normal(loc=0, scale=1, size=1000)
        
        # Run Shapiro-Wilk test
        stat, p_value = statistical_test.shapiro_wilk_test(residuals)
        
        # For normal data, p-value should be > 0.05 (fail to reject normality)
        assert p_value > 0.05, f"Normal data should have p > 0.05, got {p_value}"
        assert 0 <= stat <= 1, f"Shapiro-Wilk statistic should be between 0 and 1, got {stat}"
    
    def test_shapiro_wilk_non_normal_residuals(self):
        """Test Shapiro-Wilk test on non-normally distributed residuals."""
        # Generate exponentially distributed residuals (non-normal)
        np.random.seed(42)
        residuals = np.random.exponential(scale=1, size=1000)
        
        # Run Shapiro-Wilk test
        stat, p_value = statistical_test.shapiro_wilk_test(residuals)
        
        # For non-normal data, p-value should be < 0.05 (reject normality)
        assert p_value < 0.05, f"Non-normal data should have p < 0.05, got {p_value}"
    
    def test_select_correlation_method_normal(self):
        """Test that Pearson is selected when residuals are normal."""
        np.random.seed(42)
        residuals = np.random.normal(loc=0, scale=1, size=500)
        
        method, p_value = statistical_test.select_correlation_method(residuals)
        
        assert method == "pearson", f"Expected 'pearson' for normal residuals, got '{method}'"
        assert p_value > 0.05, "Normality test p-value should be > 0.05"
    
    def test_select_correlation_method_non_normal(self):
        """Test that Spearman is selected when residuals are non-normal."""
        np.random.seed(42)
        residuals = np.random.exponential(scale=1, size=500)
        
        method, p_value = statistical_test.select_correlation_method(residuals)
        
        assert method == "spearman", f"Expected 'spearman' for non-normal residuals, got '{method}'"
        assert p_value < 0.05, "Normality test p-value should be < 0.05"
    
    def test_calculate_correlation_pearson(self):
        """Test Pearson correlation calculation."""
        np.random.seed(42)
        x = np.random.normal(loc=0, scale=1, size=100)
        y = 2 * x + np.random.normal(loc=0, scale=0.5, size=100)  # Strong positive correlation
        
        r, p_value = statistical_test.calculate_correlation(x, y, method="pearson")
        
        assert -1 <= r <= 1, f"Correlation coefficient should be between -1 and 1, got {r}"
        assert 0 <= p_value <= 1, f"P-value should be between 0 and 1, got {p_value}"
        assert r > 0.7, f"Expected strong positive correlation, got {r}"
    
    def test_calculate_correlation_spearman(self):
        """Test Spearman correlation calculation."""
        np.random.seed(42)
        x = np.random.exponential(scale=1, size=100)
        y = 2 * x + np.random.exponential(scale=0.5, size=100)  # Monotonic relationship
        
        r, p_value = statistical_test.calculate_correlation(x, y, method="spearman")
        
        assert -1 <= r <= 1, f"Correlation coefficient should be between -1 and 1, got {r}"
        assert 0 <= p_value <= 1, f"P-value should be between 0 and 1, got {p_value}"
        assert r > 0.7, f"Expected strong positive correlation, got {r}"
    
    def test_determine_significance(self):
        """Test significance flag determination."""
        # Significant case
        assert statistical_test.determine_significance(0.01) is True
        assert statistical_test.determine_significance(0.049) is True
        
        # Non-significant case
        assert statistical_test.determine_significance(0.051) is False
        assert statistical_test.determine_significance(0.5) is False
    
    def test_full_analysis_pipeline(self):
        """Test the complete statistical analysis pipeline."""
        # Create temporary directory for test outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data
            np.random.seed(42)
            n_samples = 200
            
            # Generate control_proxy and anxiety_score with known correlation
            control_proxy = np.random.normal(loc=0.5, scale=0.2, size=n_samples)
            # Negative correlation: higher control -> lower anxiety
            anxiety_score = 0.8 - 0.5 * control_proxy + np.random.normal(loc=0, scale=0.1, size=n_samples)
            
            # Create DataFrame
            df = pd.DataFrame({
                'post_id': range(n_samples),
                'control_proxy': control_proxy,
                'anxiety_score': anxiety_score
            })
            
            # Save to CSV
            test_data_path = temp_path / "final_analysis.csv"
            df.to_csv(test_data_path, index=False)
            
            # Run the full pipeline
            results = statistical_test.run_statistical_analysis_pipeline(
                input_path=str(test_data_path),
                output_dir=str(temp_path)
            )
            
            # Verify results structure
            assert 'correlation_method' in results
            assert 'correlation_coefficient' in results
            assert 'p_value' in results
            assert 'is_significant' in results
            assert 'normality_p_value' in results
            
            # Verify results content
            assert results['correlation_method'] in ['pearson', 'spearman']
            assert -1 <= results['correlation_coefficient'] <= 1
            assert 0 <= results['p_value'] <= 1
            assert isinstance(results['is_significant'], bool)
            assert 0 <= results['normality_p_value'] <= 1
            
            # Verify output files were created
            assert (temp_path / "normality_check.json").exists()
            assert (temp_path / "analysis_results.json").exists()
            
            # Verify the correlation is negative (as we constructed the data)
            assert results['correlation_coefficient'] < 0, "Expected negative correlation"
            
            # Verify significance (our constructed data should be significant)
            assert results['is_significant'] is True, "Expected significant correlation"
    
    def test_edge_case_small_sample(self):
        """Test behavior with small sample size."""
        np.random.seed(42)
        residuals = np.random.normal(loc=0, scale=1, size=20)
        
        # Should not raise an error
        stat, p_value = statistical_test.shapiro_wilk_test(residuals)
        assert 0 <= stat <= 1
        assert 0 <= p_value <= 1
    
    def test_edge_case_perfect_correlation(self):
        """Test correlation with perfect linear relationship."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect positive correlation
        
        r, p_value = statistical_test.calculate_correlation(x, y, method="pearson")
        
        assert abs(r) == 1.0, f"Expected perfect correlation, got {r}"
        assert p_value == 0.0, f"Expected p=0 for perfect correlation, got {p_value}"
    
    def test_file_output_format(self):
        """Test that output files are valid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal test data
            df = pd.DataFrame({
                'post_id': [1, 2, 3],
                'control_proxy': [0.1, 0.2, 0.3],
                'anxiety_score': [0.8, 0.7, 0.6]
            })
            
            test_data_path = temp_path / "final_analysis.csv"
            df.to_csv(test_data_path, index=False)
            
            # Run pipeline
            statistical_test.run_statistical_analysis_pipeline(
                input_path=str(test_data_path),
                output_dir=str(temp_path)
            )
            
            # Verify JSON files are valid
            with open(temp_path / "normality_check.json", 'r') as f:
                normality_data = json.load(f)
                assert 'normality_p_value' in normality_data
            
            with open(temp_path / "analysis_results.json", 'r') as f:
                analysis_data = json.load(f)
                assert 'correlation_coefficient' in analysis_data
                assert 'p_value' in analysis_data
                assert 'is_significant' in analysis_data
                assert 'correlation_method' in analysis_data
