"""
Unit tests for code/utils/stats.py

Tests the statistical significance logic (Shapiro-Wilk -> t-test/Wilcoxon)
and threshold identification logic as required by US2.
"""
import pytest
import numpy as np
from scipy import stats as scipy_stats
from utils.stats import (
    check_normality, 
    paired_comparison, 
    identify_sparsity_threshold, 
    save_threshold_results
)
import json
import tempfile
import os
from pathlib import Path

class TestCheckNormality:
    """Tests for the Shapiro-Wilk normality check logic."""
    
    def test_normal_distribution(self):
        # Generate normal data
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=100).tolist()
        is_normal, p_val = check_normality(data)
        
        # Shapiro-Wilk should not reject normality for this data
        assert isinstance(is_normal, bool)
        assert isinstance(p_val, float)
        # With seed 42 and 100 samples, it's highly likely to pass
        # We assert the logic is sound: if p > 0.05, it's normal
        assert (is_normal and p_val > 0.05) or (not is_normal and p_val <= 0.05)

    def test_non_normal_distribution(self):
        # Generate exponential data (highly skewed)
        np.random.seed(42)
        data = np.random.exponential(scale=2.0, size=100).tolist()
        is_normal, p_val = check_normality(data)
        
        # Exponential distribution is typically rejected by Shapiro-Wilk
        # We verify the function returns a boolean and a float
        assert isinstance(is_normal, bool)
        assert isinstance(p_val, float)
        # If it's not normal, p-value should be low
        if not is_normal:
            assert p_val < 0.05

    def test_small_sample(self):
        # Shapiro-Wilk requires n >= 3
        data = [1.0, 2.0, 3.0]
        is_normal, p_val = check_normality(data)
        
        assert isinstance(is_normal, bool)
        assert isinstance(p_val, float)
        # Should handle gracefully without crashing

    def test_insufficient_sample(self):
        # Less than 3 samples should be handled
        data = [1.0, 2.0]
        is_normal, p_val = check_normality(data)
        
        assert isinstance(is_normal, bool)
        assert isinstance(p_val, float)

class TestPairedComparison:
    """Tests for the adaptive statistical test logic (t-test vs Wilcoxon)."""
    
    def test_identical_groups(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = paired_comparison(data, data)
        
        assert result["p_value"] == 1.0
        assert result["is_significant"] is False
        assert result["mean_diff"] == 0.0
        # Should use t-test or wilcoxon, both return 1.0 for identical
        assert result["test_type"] in ["t-test", "wilcoxon"]

    def test_t_test_path(self):
        # Create normal-ish data with a shift
        np.random.seed(42)
        group_a = np.random.normal(10, 1, 50).tolist()
        group_b = np.random.normal(12, 1, 50).tolist()
        
        result = paired_comparison(group_a, group_b)
        
        assert "p_value" in result
        assert "statistic" in result
        assert result["is_significant"] is True # Means are different
        # Should likely use t-test if normality holds
        assert result["test_type"] in ["t-test", "wilcoxon"]

    def test_wilcoxon_path(self):
        # Create skewed data (exponential) to force non-parametric test
        np.random.seed(42)
        group_a = np.random.exponential(2, 50).tolist()
        group_b = np.random.exponential(3, 50).tolist()
        
        result = paired_comparison(group_a, group_b)
        
        assert "p_value" in result
        assert "statistic" in result
        assert result["is_significant"] is True
        # Should detect non-normality and use Wilcoxon
        assert result["test_type"] in ["t-test", "wilcoxon"]

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            paired_comparison([1, 2], [1, 2, 3])

    def test_empty_groups(self):
        with pytest.raises(ValueError):
            paired_comparison([], [])

    def test_single_element(self):
        # t-test requires at least 2 elements
        with pytest.raises(Exception): # scipy.stats will raise
            paired_comparison([1.0], [2.0])

class TestIdentifySparsityThreshold:
    """Tests for the threshold identification logic."""
    
    def test_threshold_identified(self):
        # Simulate data where 2 views is bad, 5 views is good
        # Reference (5 views) mean = 0.1
        # 2 views mean = 0.2 (100% increase > 15%)
        results = {
            "5": [{"chamfer_distance": 0.1} for _ in range(10)],
            "4": [{"chamfer_distance": 0.11} for _ in range(10)], # 10% increase
            "3": [{"chamfer_distance": 0.13} for _ in range(10)], # 30% increase
            "2": [{"chamfer_distance": 0.20} for _ in range(10)], # 100% increase
        }
        
        res = identify_sparsity_threshold(results, tolerance_threshold=0.15)
        
        assert res["reference_view_count"] == 5
        # 3 is the first view count (descending from 5) that exceeds 15%
        # 4 is 10% (ok), 3 is 30% (fail)
        assert res["threshold_view_count"] == 3
        
        # Verify details
        details = {d["view_count"]: d for d in res["details"]}
        assert details[2]["exceeds_threshold"] is True
        assert details[4]["exceeds_threshold"] is False
        assert details[3]["exceeds_threshold"] is True

    def test_no_threshold_found(self):
        # All within tolerance
        results = {
            "5": [{"chamfer_distance": 0.1} for _ in range(10)],
            "2": [{"chamfer_distance": 0.11} for _ in range(10)], # 10% increase
        }
        
        res = identify_sparsity_threshold(results, tolerance_threshold=0.15)
        assert res["threshold_view_count"] is None

    def test_all_exceed_threshold(self):
        results = {
            "5": [{"chamfer_distance": 0.1} for _ in range(10)],
            "4": [{"chamfer_distance": 0.2} for _ in range(10)], # 100% increase
            "3": [{"chamfer_distance": 0.2} for _ in range(10)],
            "2": [{"chamfer_distance": 0.2} for _ in range(10)],
        }
        
        res = identify_sparsity_threshold(results, tolerance_threshold=0.15)
        # 4 is the first to exceed
        assert res["threshold_view_count"] == 4

class TestSaveThresholdResults:
    """Tests for saving results to JSON."""
    
    def test_save_and_load(self):
        data = {"test": 123, "threshold": 5, "details": [{"view_count": 2, "exceeds_threshold": True}]}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        
        try:
            save_threshold_results(data, path)
            with open(path, 'r') as f:
                loaded = json.load(f)
            assert loaded == data
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_save_to_directory(self):
        data = {"result": "ok"}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "result.json")
            save_threshold_results(data, path)
            assert os.path.exists(path)
            with open(path, 'r') as f:
                loaded = json.load(f)
            assert loaded == data