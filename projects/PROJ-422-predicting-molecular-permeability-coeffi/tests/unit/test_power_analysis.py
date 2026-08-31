"""
Unit tests for the post-hoc power analysis module.

These tests verify the correctness of power calculation logic
without requiring real model outputs.
"""
import pytest
import json
import tempfile
from pathlib import Path
import numpy as np
from scipy import stats

# Import the module under test
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.power_analysis import (
    load_metrics,
    calculate_noncentrality_parameter,
    calculate_power,
    run_power_analysis,
    save_power_analysis
)

class TestCalculateNoncentralityParameter:
    """Tests for non-centrality parameter calculation."""
    
    def test_basic_calculation(self):
        """Test basic ncp calculation: ncp = d * sqrt(n)"""
        d = 0.5
        n = 100
        expected = 0.5 * np.sqrt(100)
        
        result = calculate_noncentrality_parameter(d, n)
        assert np.isclose(result, expected)
        
    def test_large_effect_size(self):
        """Test with large effect size."""
        d = 0.8
        n = 50
        expected = 0.8 * np.sqrt(50)
        
        result = calculate_noncentrality_parameter(d, n)
        assert np.isclose(result, expected)
        
    def test_small_sample(self):
        """Test with small sample size."""
        d = 0.3
        n = 10
        expected = 0.3 * np.sqrt(10)
        
        result = calculate_noncentrality_parameter(d, n)
        assert np.isclose(result, expected)

class TestCalculatePower:
    """Tests for power calculation."""
    
    def test_high_power_large_sample(self):
        """Test that large sample with moderate effect yields high power."""
        ncp = 2.0  # Large ncp
        n = 100
        alpha = 0.05
        
        power = calculate_power(ncp, n, alpha, 'two-sided')
        assert power > 0.80
        
    def test_low_power_small_sample(self):
        """Test that small sample with small effect yields low power."""
        ncp = 0.5  # Small ncp
        n = 20
        alpha = 0.05
        
        power = calculate_power(ncp, n, alpha, 'two-sided')
        assert power < 0.60
        
    def test_alternative_greater(self):
        """Test one-sided greater test."""
        ncp = 1.5
        n = 50
        alpha = 0.05
        
        power = calculate_power(ncp, n, alpha, 'greater')
        assert 0 < power < 1
        
    def test_alternative_less(self):
        """Test one-sided less test."""
        ncp = -1.5
        n = 50
        alpha = 0.05
        
        power = calculate_power(ncp, n, alpha, 'less')
        assert 0 < power < 1
        
    def test_invalid_alternative(self):
        """Test that invalid alternative raises error."""
        with pytest.raises(ValueError):
            calculate_power(1.0, 50, 0.05, 'invalid')

class TestRunPowerAnalysis:
    """Tests for the main power analysis function."""
    
    def test_full_analysis(self):
        """Test complete power analysis flow."""
        cohen_d = 0.5
        n = 100
        
        results = run_power_analysis(cohen_d, n)
        
        assert "power" in results
        assert "effect_size_cohen_d" in results
        assert "sample_size" in results
        assert "alpha_level" in results
        assert "interpretation" in results
        assert "sample_adequacy" in results
        
        # Check values
        assert results["effect_size_cohen_d"] == 0.5
        assert results["sample_size"] == 100
        assert results["alpha_level"] == 0.05
        assert 0 <= results["power"] <= 1
        
    def test_interpretation_high_power(self):
        """Test interpretation for high power."""
        # High power scenario
        results = run_power_analysis(cohen_d=0.8, n=200)
        assert "Adequate" in results["interpretation"]
        
    def test_interpretation_low_power(self):
        """Test interpretation for low power."""
        # Low power scenario
        results = run_power_analysis(cohen_d=0.2, n=20)
        assert "Low" in results["interpretation"]

class TestLoadMetrics:
    """Tests for loading metrics file."""
    
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        metrics_data = {
            "paired_ttest": {
                "cohen_d": 0.5,
                "sample_size": 100
            }
        }
        
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
            
        result = load_metrics(metrics_file)
        assert result == metrics_data
        
    def test_file_not_found(self, tmp_path):
        """Test error when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_metrics(tmp_path / "nonexistent.json")

class TestSavePowerAnalysis:
    """Tests for saving power analysis results."""
    
    def test_save_valid_results(self, tmp_path):
        """Test saving valid results."""
        results = {
            "power": 0.85,
            "effect_size_cohen_d": 0.5,
            "sample_size": 100
        }
        
        output_file = tmp_path / "power_analysis.json"
        save_power_analysis(results, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
            
        assert saved_data == results
        
    def test_create_parent_directories(self, tmp_path):
        """Test that parent directories are created if needed."""
        results = {"power": 0.8}
        
        nested_file = tmp_path / "subdir" / "results" / "power_analysis.json"
        save_power_analysis(results, nested_file)
        
        assert nested_file.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])