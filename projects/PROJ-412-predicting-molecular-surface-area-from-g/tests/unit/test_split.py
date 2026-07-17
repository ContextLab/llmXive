"""
Unit tests for data splitting logic (T015).
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import csv
import json

# Mock the project root and data dir imports
from utils.config import get_project_root, get_data_dir

# Import functions to test
# We need to import the logic, not necessarily the main() which does I/O
# Assuming split.py is in code/data/split.py
import sys
import os
# Ensure we can import code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.split import (
    calculate_mw_stats, 
    stratified_split_by_mw, 
    validate_split_distribution,
    save_indices_to_csv,
    SplitResult
)


class TestCalculateMwStats:
    def test_basic_stats(self):
        data = [100.0, 200.0, 300.0]
        stats = calculate_mw_stats(data)
        assert stats["mean"] == 200.0
        assert stats["std"] == pytest.approx(81.6496580927726)
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0
        assert stats["count"] == 3

    def test_single_value(self):
        data = [50.0]
        stats = calculate_mw_stats(data)
        assert stats["mean"] == 50.0
        assert stats["std"] == 0.0
        assert stats["count"] == 1


class TestStratifiedSplitByMw:
    def test_split_ratio(self):
        # Create a synthetic distribution where we know the split
        # 100 molecules, MW 100 to 200
        mw_values = list(range(100, 200))
        train_idx, test_idx = stratified_split_by_mw(mw_values, train_ratio=0.8, seed=42)
        
        total = len(train_idx) + len(test_idx)
        assert total == 100
        assert len(train_idx) == 80
        assert len(test_idx) == 20

    def test_no_overlap(self):
        mw_values = [float(i) for i in range(100)]
        train_idx, test_idx = stratified_split_by_mw(mw_values, seed=42)
        
        assert set(train_idx).isdisjoint(set(test_idx))
        assert len(set(train_idx)) == len(train_idx)
        assert len(set(test_idx)) == len(test_idx)

    def test_seed_reproducibility(self):
        mw_values = [float(i) for i in range(50)]
        train1, test1 = stratified_split_by_mw(mw_values, seed=123)
        train2, test2 = stratified_split_by_mw(mw_values, seed=123)
        
        assert train1 == train2
        assert test1 == test2


class TestValidateSplitDistribution:
    def test_identical_distributions(self):
        data = [100.0, 101.0, 102.0, 103.0, 104.0]
        train, test = data[:3], data[3:] # Small sample, might be noisy but logic holds
        # Actually, for KS test we need larger samples to be confident
        # Let's create two identical large samples
        large_data = np.random.normal(100, 10, 1000)
        train = large_data[:500]
        test = large_data[500:]
        
        stat, p_val, passed = validate_split_distribution(train, test, threshold=0.05)
        # With identical distributions, p-value should be high
        assert passed is True

    def test_different_distributions(self):
        # Create two distinct distributions
        train = np.random.normal(100, 5, 1000)
        test = np.random.normal(150, 5, 1000)
        
        stat, p_val, passed = validate_split_distribution(train, test, threshold=0.05)
        # With very different means, p-value should be near 0
        assert passed is False
        assert stat > 0.5 # Expect high statistic


class TestSaveIndicesToCsv:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            train_idx = [1, 2, 3]
            test_idx = [4, 5]
            
            train_file, test_file = save_indices_to_csv(train_idx, test_idx, output_path)
            
            assert train_file.exists()
            assert test_file.exists()
            
            # Verify content
            with open(train_file, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                assert header == ['index']
                rows = [int(r[0]) for r in reader]
                assert rows == train_idx
            
            with open(test_file, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                assert header == ['index']
                rows = [int(r[0]) for r in reader]
                assert rows == test_idx