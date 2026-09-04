"""
Unit tests for statistical analysis module (stats.py).

Tests cover:
- One-sample t-test implementation correctness
- Edge cases (zero variance, small samples)
- Data loading and validation
"""
import pytest
import numpy as np
from pathlib import Path
import json
import tempfile
from unittest.mock import patch

from models.stats import (
    perform_one_sample_ttest,
    load_delta_data,
    analyze_delta_distributions,
    run_statistical_tests,
    ValidationFailedError
)
from utils.schema_validation import OneSampleTTestResult


class TestOneSampleTTest:
    """Tests for the one-sample t-test implementation."""
    
    def test_known_dataset_returns_correct_statistic(self):
        """
        Test that t-test returns correct values for a known dataset.
        
        Using a simple dataset where we can manually verify:
        Data: [1, 2, 3, 4, 5]
        Mean: 3
        Std (ddof=1): ~1.58
        n: 5
        Standard Error: ~0.707
        t-statistic (vs 0): 3 / 0.707 ≈ 4.24
        """
        data = [1, 2, 3, 4, 5]
        result = perform_one_sample_ttest(data, null_mean=0.0, alpha=0.05)
        
        # Verify result type
        assert isinstance(result, OneSampleTTestResult)
        
        # Verify sample size
        assert result.sample_size == 5
        
        # Verify mean
        assert abs(result.mean_delta - 3.0) < 0.001
        
        # Verify standard deviation (ddof=1)
        expected_std = np.std(data, ddof=1)
        assert abs(result.std_delta - expected_std) < 0.001
        
        # Verify t-statistic is positive (mean > 0)
        assert result.t_statistic > 0
        
        # Verify p-value is small (significant result)
        assert result.p_value < 0.05
        assert result.significant
    
    def test_symmetric_around_zero_returns_non_significant(self):
        """Test that data symmetric around zero is not significant."""
        data = [-2, -1, 0, 1, 2]
        result = perform_one_sample_ttest(data, null_mean=0.0, alpha=0.05)
        
        # Mean should be 0
        assert abs(result.mean_delta) < 0.001
        
        # Should not be significant (p > 0.05)
        assert not result.significant
        assert result.p_value > 0.05
    
    def test_insufficient_data_raises_error(self):
        """Test that less than 2 data points raises an error."""
        with pytest.raises(ValidationFailedError):
            perform_one_sample_ttest([1.0], null_mean=0.0)
        
        with pytest.raises(ValidationFailedError):
            perform_one_sample_ttest([], null_mean=0.0)
    
    def test_zero_variance_all_zeros(self):
        """Test behavior when all values are exactly zero."""
        data = [0.0, 0.0, 0.0, 0.0, 0.0]
        result = perform_one_sample_ttest(data, null_mean=0.0)
        
        # t-statistic should be 0, p-value should be 1.0
        assert result.t_statistic == 0.0
        assert result.p_value == 1.0
        assert not result.significant
    
    def test_zero_variance_non_zero_mean(self):
        """Test behavior when all values are identical but non-zero."""
        data = [2.0, 2.0, 2.0, 2.0]
        result = perform_one_sample_ttest(data, null_mean=0.0)
        
        # Should be highly significant (all values = 2, null = 0)
        assert result.significant
        assert result.p_value < 0.05
        assert abs(result.mean_delta - 2.0) < 0.001
    
    def test_large_sample_size(self):
        """Test with a larger dataset."""
        np.random.seed(42)
        data = np.random.normal(loc=0.5, scale=1.0, size=1000).tolist()
        result = perform_one_sample_ttest(data, null_mean=0.0)
        
        # Should detect the shift from 0
        assert result.significant
        assert result.sample_size == 1000


class TestLoadDeltaData:
    """Tests for delta data loading functionality."""
    
    def test_loads_valid_json_file(self):
        """Test loading from a valid JSON file."""
        # Create temporary file with valid data
        test_data = [
            {
                "hash": "abc123",
                "deltas": {
                    "complexity_delta": -1.0,
                    "pylint_delta": -5.0,
                    "maintainability_delta": 2.0
                }
            },
            {
                "hash": "def456",
                "deltas": {
                    "complexity_delta": -0.5,
                    "pylint_delta": -3.0,
                    "maintainability_delta": 1.5
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            result = load_delta_data(temp_path)
            
            assert "complexity_delta" in result
            assert "pylint_delta" in result
            assert "maintainability_delta" in result
            
            assert len(result["complexity_delta"]) == 2
            assert len(result["pylint_delta"]) == 2
            assert len(result["maintainability_delta"]) == 2
        finally:
            temp_path.unlink()
    
    def test_handles_missing_deltas_key(self):
        """Test that records without 'deltas' key are skipped."""
        test_data = [
            {
                "hash": "abc123",
                "deltas": {"complexity_delta": -1.0}
            },
            {
                "hash": "def456"
                # Missing 'deltas' key
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            result = load_delta_data(temp_path)
            
            # Should only have one valid entry
            assert len(result["complexity_delta"]) == 1
        finally:
            temp_path.unlink()
    
    def test_handles_invalid_delta_values(self):
        """Test that invalid delta values are skipped."""
        test_data = [
            {
                "hash": "abc123",
                "deltas": {
                    "complexity_delta": -1.0,
                    "pylint_delta": "invalid",
                    "maintainability_delta": None
                }
            },
            {
                "hash": "def456",
                "deltas": {
                    "complexity_delta": -0.5,
                    "pylint_delta": 3.0,
                    "maintainability_delta": 1.5
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            result = load_delta_data(temp_path)
            
            # Should have 2 complexity values, 1 pylint, 1 maintainability
            assert len(result["complexity_delta"]) == 2
            assert len(result["pylint_delta"]) == 1
            assert len(result["maintainability_delta"]) == 1
        finally:
            temp_path.unlink()
    
    def test_raises_error_on_missing_file(self):
        """Test that missing file raises ValidationFailedError."""
        with pytest.raises(ValidationFailedError):
            load_delta_data(Path("nonexistent_file.json"))
    
    def test_raises_error_on_empty_data(self):
        """Test that empty data raises ValidationFailedError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValidationFailedError):
                load_delta_data(temp_path)
        finally:
            temp_path.unlink()
    
    def test_raises_error_on_non_list_data(self):
        """Test that non-list data raises ValidationFailedError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValidationFailedError):
                load_delta_data(temp_path)
        finally:
            temp_path.unlink()


class TestStatisticalAnalysisIntegration:
    """Integration tests for the full statistical analysis pipeline."""
    
    def test_full_analysis_produces_valid_results(self):
        """Test that full analysis produces valid StatisticalTests object."""
        # Create test data
        test_data = []
        for i in range(50):
            test_data.append({
                "hash": f"sample_{i:03d}",
                "deltas": {
                    "complexity_delta": np.random.normal(-0.5, 1.0),
                    "pylint_delta": np.random.normal(-3.0, 5.0),
                    "maintainability_delta": np.random.normal(1.0, 2.0)
                }
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_input = Path(f.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_output = Path(f.name)
        
        try:
            results = run_statistical_tests(
                data_path=temp_input,
                output_path=temp_output,
                alpha=0.05
            )
            
            # Verify results structure
            assert "complexity" in results
            assert "pylint" in results
            assert "maintainability" in results
            assert "summary" in results
            
            # Verify summary
            assert results["summary"]["total_tests"] == 3
            assert results["summary"]["alpha"] == 0.05
            assert "significant_results" in results["summary"]
            
            # Verify output file was created
            assert temp_output.exists()
            
            # Verify output file content
            with open(temp_output, 'r') as f:
                saved_results = json.load(f)
                assert saved_results == results
        finally:
            temp_input.unlink()
            if temp_output.exists():
                temp_output.unlink()