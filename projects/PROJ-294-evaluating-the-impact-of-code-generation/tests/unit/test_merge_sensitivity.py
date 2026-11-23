"""
Unit tests for T045: merge_sensitivity_metrics.py
"""
import pytest
import json
import os
import tempfile
import shutil
from code.merge_sensitivity_metrics import (
    calculate_effect_size_difference,
    merge_metrics,
    load_existing_metrics,
    save_metrics
)

class TestEffectSize:
    def test_cohens_d_identical_groups(self):
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0, 3.0]
        result = calculate_effect_size_difference(group1, group2)
        assert abs(result['cohens_d']) < 1e-6
        assert result['delta'] == 0.0

    def test_cohens_d_different_means(self):
        # Mean1 = 10, Mean2 = 0. Var1=0, Var2=0 (simplified for perfect separation)
        # Pooled std = 0 -> d undefined/infinite? 
        # Let's use non-zero variance
        group1 = [10.0, 10.0, 10.0]
        group2 = [0.0, 0.0, 0.0]
        # This will result in pooled_std = 0 if we don't handle it, but mathematically:
        # var1=0, var2=0 -> pooled_var=0 -> div by zero. 
        # Our function returns 0.0 for cohens_d if pooled_std is 0.
        result = calculate_effect_size_difference(group1, group2)
        # In this specific edge case of 0 variance, our implementation returns 0
        assert result['delta'] == 10.0
        # The implementation handles div by zero by returning 0.0
        assert result['cohens_d'] == 0.0

    def test_cohens_d_normal_case(self):
        # Group 1: mean 10, std ~1. Group 2: mean 0, std ~1
        group1 = [9, 10, 11]
        group2 = [-1, 0, 1]
        result = calculate_effect_size_difference(group1, group2)
        # Mean diff = 10
        # Var1 = 1, Var2 = 1 -> Pooled Var = 1 -> Pooled Std = 1
        # d = 10 / 1 = 10
        assert abs(result['cohens_d'] - 10.0) < 0.1
        assert result['delta'] == 10.0

class TestMergeMetrics:
    def test_merge_empty_new(self):
        existing = [{"task_id": "1", "source": "A"}]
        new_samples = []
        merged = merge_metrics(existing, new_samples)
        assert len(merged) == 1
        assert merged[0]["task_id"] == "1"

    def test_merge_append_new(self):
        existing = [{"task_id": "1", "source": "A"}]
        new_samples = [{"task_id": "1", "source": "B"}]
        merged = merge_metrics(existing, new_samples)
        assert len(merged) == 2
        # Check both are present
        sources = [m["source"] for m in merged]
        assert "A" in sources
        assert "B" in sources

    def test_merge_multiple_new(self):
        existing = [{"task_id": "1", "source": "A"}]
        new_samples = [
            {"task_id": "1", "source": "B"},
            {"task_id": "2", "source": "B"}
        ]
        merged = merge_metrics(existing, new_samples)
        assert len(merged) == 3
        task_ids = [m["task_id"] for m in merged]
        assert task_ids.count("1") == 2
        assert task_ids.count("2") == 1

class TestIO:
    def test_save_and_load_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            data = [{"task_id": "1", "val": 10}]
            save_metrics(data, filepath)
            assert os.path.exists(filepath)
            loaded = load_existing_metrics(filepath)
            assert loaded == data