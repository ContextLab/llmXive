"""
Unit tests for statistical comparison module.
"""
import pytest
import numpy as np
import json
import tempfile
import csv
from pathlib import Path

from models.statistical_comparison import (
    shapiro_wilk_test,
    wilcoxon_signed_rank_test,
    corrected_resampled_ttest,
    run_statistical_comparison
)

class TestShapiroWilk:
    def test_normal_distribution(self):
        """Test with normally distributed data."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100).tolist()
        
        result = shapiro_wilk_test(normal_data)
        
        assert 'is_normal' in result
        assert 'statistic' in result
        assert 'p_value' in result
        assert result['is_normal'] is True  # Normal data should pass
    
    def test_non_normal_distribution(self):
        """Test with exponentially distributed data."""
        np.random.seed(42)
        non_normal_data = np.random.exponential(scale=1, size=100).tolist()
        
        result = shapiro_wilk_test(non_normal_data)
        
        assert 'is_normal' in result
        assert 'statistic' in result
        assert 'p_value' in result
        # Exponential data is typically non-normal
        assert result['is_normal'] is False
    
    def test_insufficient_data(self):
        """Test with too few data points."""
        result = shapiro_wilk_test([1.0, 2.0])
        
        assert result['is_normal'] is False
        assert 'message' in result
        assert 'Insufficient' in result['message']

class TestWilcoxon:
    def test_equal_lists(self):
        """Test Wilcoxon with equal length lists."""
        np.random.seed(42)
        a = np.random.normal(0, 1, 50).tolist()
        b = np.random.normal(0.5, 1, 50).tolist()
        
        result = wilcoxon_signed_rank_test(a, b)
        
        assert 'method' in result
        assert result['method'] == 'wilcoxon_signed_rank'
        assert 'statistic' in result
        assert 'p_value' in result
    
    def test_unequal_lists_raises_error(self):
        """Test that unequal lists raise an error."""
        with pytest.raises(ValueError):
            wilcoxon_signed_rank_test([1, 2, 3], [1, 2])

class TestCorrectedResampledTtest:
    def test_basic_execution(self):
        """Test basic execution of corrected resampled t-test."""
        np.random.seed(42)
        a = np.random.normal(0, 1, 100).tolist()
        b = np.random.normal(0.1, 1, 100).tolist()
        
        result = corrected_resampled_ttest(a, b, n_iterations=100)
        
        assert 'method' in result
        assert result['method'] == 'corrected_resampled_ttest'
        assert 'p_value' in result
        assert 'confidence_interval' in result
        assert len(result['confidence_interval']) == 2
    
    def test_unequal_lists_raises_error(self):
        """Test that unequal lists raise an error."""
        with pytest.raises(ValueError):
            corrected_resampled_ttest([1, 2, 3], [1, 2])

class TestRunStatisticalComparison:
    def test_full_pipeline_normal(self):
        """Test full pipeline with normal residuals."""
        np.random.seed(42)
        a = np.random.normal(0, 1, 100).tolist()
        b = np.random.normal(0.1, 1, 100).tolist()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = run_statistical_comparison(
                residuals_a=a,
                residuals_b=b,
                model_name_a="Model A",
                model_name_b="Model B",
                output_path=output_path
            )
            
            assert 'comparison' in result
            assert 'test_used' in result
            assert 'test_results' in result
            assert 'conclusion' in result
            assert result['test_used'] in ['wilcoxon_signed_rank', 'corrected_resampled_ttest']
            
            # Check file was created
            assert output_path.exists()
            
            # Check JSON is valid
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded == result
        finally:
            output_path.unlink()
    
    def test_full_pipeline_non_normal(self):
        """Test full pipeline with non-normal residuals."""
        np.random.seed(42)
        a = np.random.exponential(1, 100).tolist()
        b = np.random.exponential(1.1, 100).tolist()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = run_statistical_comparison(
                residuals_a=a,
                residuals_b=b,
                model_name_a="Exp Model A",
                model_name_b="Exp Model B",
                output_path=output_path
            )
            
            # With exponential data, we expect Wilcoxon to be used
            assert 'test_used' in result
            assert result['test_used'] == 'wilcoxon_signed_rank'
            assert 'conclusion' in result
        finally:
            output_path.unlink()
    
    def test_csv_input_output(self):
        """Test reading from CSV files and writing JSON output."""
        np.random.seed(42)
        a = np.random.normal(0, 1, 50).tolist()
        b = np.random.normal(0.2, 1, 50).tolist()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            csv_a = tmpdir / "residuals_a.csv"
            csv_b = tmpdir / "residuals_b.csv"
            output_json = tmpdir / "comparison.json"
            
            # Write CSVs
            with open(csv_a, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['residual'])
                writer.writeheader()
                for val in a:
                    writer.writerow({'residual': val})
            
            with open(csv_b, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['residual'])
                writer.writeheader()
                for val in b:
                    writer.writerow({'residual': val})
            
            # Run comparison
            result = run_statistical_comparison(
                residuals_a=a,
                residuals_b=b,
                model_name_a="CSV Model A",
                model_name_b="CSV Model B",
                output_path=output_json
            )
            
            assert output_json.exists()
            with open(output_json, 'r') as f:
                loaded = json.load(f)
                assert loaded['comparison'] == "CSV Model A vs CSV Model B"