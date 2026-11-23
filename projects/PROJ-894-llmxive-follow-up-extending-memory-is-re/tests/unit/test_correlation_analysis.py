"""
Unit tests for correlation_analysis.py (T025).
"""

import os
import json
import tempfile
import csv
from pathlib import Path
import numpy as np
import pytest

from analysis.correlation_analysis import calculate_point_biserial, load_results_from_csv

class TestCalculatePointBiserial:
    def test_perfect_positive_correlation(self):
        # X increases as Y goes from 0 to 1
        x = np.array([1, 2, 3, 10, 11, 12])
        y = np.array([0, 0, 0, 1, 1, 1])
        r, p = calculate_point_biserial(x, y)
        # Should be positive
        assert r > 0.5
        assert p < 0.05

    def test_perfect_negative_correlation(self):
        # X decreases as Y goes from 0 to 1
        x = np.array([10, 11, 12, 1, 2, 3])
        y = np.array([0, 0, 0, 1, 1, 1])
        r, p = calculate_point_biserial(x, y)
        # Should be negative
        assert r < -0.5
        assert p < 0.05

    def test_no_variance_in_y(self):
        # All y are 0
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([0, 0, 0, 0, 0])
        r, p = calculate_point_biserial(x, y)
        assert np.isnan(r)
        assert np.isnan(p)

    def test_empty_arrays(self):
        x = np.array([])
        y = np.array([])
        r, p = calculate_point_biserial(x, y)
        assert np.isnan(r)
        assert np.isnan(p)

    def test_zero_variance_in_x(self):
        x = np.array([5, 5, 5, 5, 5])
        y = np.array([0, 0, 1, 1, 1])
        r, p = calculate_point_biserial(x, y)
        assert np.isnan(r)
        assert np.isnan(p)

class TestLoadResultsFromCsv:
    def test_load_valid_csv(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'nodes_visited', 'accuracy', 'status'])
            writer.writerow(['t1', '10', '0.8', 'success'])
            writer.writerow(['t2', '20', '0.4', 'failure'])
            writer.writerow(['t3', '15', '100%', 'success']) # Test percentage

        results = load_results_from_csv(str(csv_path))
        assert len(results) == 3
        assert results[0]['nodes_visited'] == 10
        assert results[0]['success'] == 1
        assert results[1]['success'] == 0
        assert results[2]['success'] == 1 # 100% -> 1.0 -> success

    def test_load_missing_file(self, tmp_path):
        results = load_results_from_csv(str(tmp_path / "nonexistent.csv"))
        assert results == []

    def test_load_invalid_accuracy(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'nodes_visited', 'accuracy', 'status'])
            writer.writerow(['t1', '10', 'invalid', 'success'])

        results = load_results_from_csv(str(csv_path))
        # Row with invalid accuracy should be skipped
        assert len(results) == 0
