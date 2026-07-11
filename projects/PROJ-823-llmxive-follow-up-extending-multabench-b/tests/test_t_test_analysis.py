"""
Tests for t-test analysis functionality.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
from scipy import stats

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from analysis.t_test_analysis import (
    check_normality,
    perform_statistical_test,
    load_conditioned_metrics,
    load_gpu_baselines,
    aggregate_conditioned_metrics
)


class TestNormalityCheck:
    def test_normal_distribution(self):
        """Test normality check with normally distributed data."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100)
        is_normal, p_value = check_normality(normal_data)
        
        assert is_normal is True
        assert p_value > 0.05  # Should not reject normality
        
    def test_non_normal_distribution(self):
        """Test normality check with non-normally distributed data."""
        # Exponential distribution is clearly non-normal
        exponential_data = np.random.exponential(scale=1, size=100)
        is_normal, p_value = check_normality(exponential_data)
        
        assert is_normal is False
        assert p_value < 0.05  # Should reject normality
        
    def test_insufficient_samples(self):
        """Test normality check with insufficient samples."""
        small_data = np.array([1.0, 2.0])
        is_normal, p_value = check_normality(small_data)
        
        assert is_normal is False
        assert p_value == 0.0


class TestStatisticalTest:
    def test_t_test_normal_data(self):
        """Test t-test with normally distributed data."""
        np.random.seed(42)
        conditioned_values = np.random.normal(loc=0.75, scale=0.05, size=30).tolist()
        baseline_value = 0.70
        
        result = perform_statistical_test(conditioned_values, baseline_value, "test_dataset")
        
        assert result['test_type'] == 't-test'
        assert result['t_statistic'] is not None
        assert result['p_value'] is not None
        assert result['is_significant'] is not None
        assert result['n_samples'] == 30
        
    def test_wilcoxon_non_normal_data(self):
        """Test Wilcoxon test with non-normally distributed data."""
        # Create skewed data
        conditioned_values = np.random.exponential(scale=0.1, size=30).tolist()
        baseline_value = 0.15
        
        result = perform_statistical_test(conditioned_values, baseline_value, "test_dataset")
        
        assert result['test_type'] == 'wilcoxon'
        assert result['t_statistic'] is not None
        assert result['p_value'] is not None
        
    def test_insufficient_data(self):
        """Test with insufficient data points."""
        conditioned_values = [0.75]  # Only one value
        baseline_value = 0.70
        
        result = perform_statistical_test(conditioned_values, baseline_value, "test_dataset")
        
        assert result['test_type'] == 'insufficient_data'
        assert result['t_statistic'] is None
        assert result['p_value'] is None
        
    def test_identical_values(self):
        """Test with identical values (cannot perform Wilcoxon)."""
        conditioned_values = [0.75, 0.75, 0.75]
        baseline_value = 0.70
        
        result = perform_statistical_test(conditioned_values, baseline_value, "test_dataset")
        
        assert result['test_type'] == 'wilcoxon_failed'
        assert 'error' in result


class TestLoaders:
    def test_load_conditioned_metrics_dict(self):
        """Test loading conditioned metrics from dict format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "dataset1": {"performance": 0.75, "dataset_id": "dataset1"},
                "dataset2": {"performance": 0.80, "dataset_id": "dataset2"}
            }, f)
            temp_path = Path(f.name)
        
        try:
            result = load_conditioned_metrics(temp_path)
            assert "dataset1" in result
            assert result["dataset1"]["performance"] == 0.75
        finally:
            temp_path.unlink()
            
    def test_load_conditioned_metrics_list(self):
        """Test loading conditioned metrics from list format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"dataset_id": "dataset1", "performance": 0.75},
                {"dataset_id": "dataset2", "performance": 0.80}
            ], f)
            temp_path = Path(f.name)
        
        try:
            result = load_conditioned_metrics(temp_path)
            assert "dataset1" in result
            assert result["dataset1"]["performance"] == 0.75
        finally:
            temp_path.unlink()
            
    def test_load_gpu_baselines(self):
        """Test loading GPU-Tuned baselines from CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("dataset_id,baseline_value,task_type\n")
            f.write("dataset1,0.70,classification\n")
            f.write("dataset2,0.85,regression\n")
            temp_path = Path(f.name)
        
        try:
            result = load_gpu_baselines(temp_path)
            assert "dataset1" in result
            assert result["dataset1"]["baseline_value"] == 0.70
            assert result["dataset1"]["task_type"] == "classification"
        finally:
            temp_path.unlink()


class TestAggregation:
    def test_aggregate_single_value(self):
        """Test aggregation of single performance value."""
        data = {"performance": 0.75}
        result = aggregate_conditioned_metrics(data, 0.70)
        assert result == [0.75]
        
    def test_aggregate_multiple_values(self):
        """Test aggregation of multiple performance values."""
        data = {
            "metrics": [
                {"performance": 0.72},
                {"performance": 0.78},
                {"performance": 0.75}
            ]
        }
        result = aggregate_conditioned_metrics(data, 0.70)
        assert len(result) == 3
        assert result == [0.72, 0.78, 0.75]
        
    def test_aggregate_empty(self):
        """Test aggregation with no performance data."""
        data = {"other_field": "value"}
        result = aggregate_conditioned_metrics(data, 0.70)
        assert result == []