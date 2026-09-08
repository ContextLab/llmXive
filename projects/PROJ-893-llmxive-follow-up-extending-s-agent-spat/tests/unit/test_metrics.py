"""
Unit tests for metric calculation (F1, Exact Match) and statistical tests.
Tests cover the logic in code/benchmark/metrics.py.
"""

import pytest
import math
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from benchmark.metrics import (
    calculate_exact_match,
    calculate_f1_score,
    calculate_latency_stats,
    compute_mcnemar_test,
    load_jsonl,
    load_csv
)


class TestExactMatch:
    """Tests for exact_match calculation."""

    def test_identical_lists(self):
        """Two identical lists should yield 1.0."""
        pred = [1, 2, 3, 4]
        true = [1, 2, 3, 4]
        assert calculate_exact_match(pred, true) == 1.0

    def test_single_mismatch(self):
        """One mismatch in a list of 4 should yield 0.75."""
        pred = [1, 2, 3, 4]
        true = [1, 2, 99, 4]
        assert calculate_exact_match(pred, true) == 0.75

    def test_all_mismatch(self):
        """All elements different should yield 0.0."""
        pred = [1, 2, 3, 4]
        true = [5, 6, 7, 8]
        assert calculate_exact_match(pred, true) == 0.0

    def test_empty_lists(self):
        """Empty lists should be considered a perfect match (1.0)."""
        assert calculate_exact_match([], []) == 1.0

    def test_length_mismatch(self):
        """Different lengths should yield 0.0."""
        pred = [1, 2, 3]
        true = [1, 2, 3, 4]
        assert calculate_exact_match(pred, true) == 0.0

    def test_string_predictions(self):
        """Should work with string comparisons."""
        pred = ["A", "B", "C"]
        true = ["A", "B", "C"]
        assert calculate_exact_match(pred, true) == 1.0

        pred = ["A", "B", "C"]
        true = ["A", "X", "C"]
        assert calculate_exact_match(pred, true) == 2/3

    def test_numeric_vs_string(self):
        """Numeric 1 vs String '1' should be a mismatch."""
        pred = [1, 2, 3]
        true = ["1", "2", "3"]
        assert calculate_exact_match(pred, true) == 0.0


class TestF1Score:
    """Tests for F1-score calculation based on binary classification."""

    def test_perfect_prediction(self):
        """Perfect TP, no FP, no FN -> F1 = 1.0."""
        pred = [1, 1, 1, 0, 0]
        true = [1, 1, 1, 0, 0]
        # TP=3, FP=0, FN=0 -> Precision=1, Recall=1 -> F1=1
        assert math.isclose(calculate_f1_score(pred, true), 1.0)

    def test_zero_precision(self):
        """All predicted positive but all false -> Precision=0 -> F1=0."""
        pred = [1, 1, 1, 1]
        true = [0, 0, 0, 0]
        # TP=0, FP=4, FN=0 -> Precision=0 -> F1=0
        assert calculate_f1_score(pred, true) == 0.0

    def test_zero_recall(self):
        """All predicted negative but all true positive -> Recall=0 -> F1=0."""
        pred = [0, 0, 0, 0]
        true = [1, 1, 1, 1]
        # TP=0, FP=0, FN=4 -> Recall=0 -> F1=0
        assert calculate_f1_score(pred, true) == 0.0

    def test_mixed_case(self):
        """Standard mixed case."""
        pred = [1, 1, 0, 0, 1]
        true = [1, 0, 0, 1, 1]
        # TP=2 (idx 0, 4), FP=1 (idx 1), FN=1 (idx 3)
        # Precision = 2/3, Recall = 2/3 -> F1 = 2/3
        expected_f1 = 2 * (2/3) * (2/3) / ((2/3) + (2/3))
        assert math.isclose(calculate_f1_score(pred, true), expected_f1)

    def test_empty_lists(self):
        """Empty lists -> F1 = 0.0 (defined behavior for no data)."""
        assert calculate_f1_score([], []) == 0.0

    def test_single_element_match(self):
        """Single element match."""
        assert calculate_f1_score([1], [1]) == 1.0

    def test_single_element_mismatch(self):
        """Single element mismatch."""
        assert calculate_f1_score([1], [0]) == 0.0

    def test_float_predictions(self):
        """Floats treated as exact values."""
        pred = [0.5, 0.5]
        true = [0.5, 0.5]
        assert calculate_f1_score(pred, true) == 1.0


class TestLatencyStats:
    """Tests for latency statistics calculation."""

    def test_basic_stats(self):
        """Verify min, max, median, mean."""
        latencies = [10, 20, 30, 40, 50]
        stats = calculate_latency_stats(latencies)
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["median"] == 30.0
        assert stats["mean"] == 30.0
        assert stats["count"] == 5

    def test_single_latency(self):
        """Single value stats."""
        stats = calculate_latency_stats([100])
        assert stats["min"] == 100.0
        assert stats["max"] == 100.0
        assert stats["median"] == 100.0
        assert stats["mean"] == 100.0
        assert stats["count"] == 1

    def test_even_count_median(self):
        """Median of even count is average of two middle values."""
        latencies = [10, 20, 30, 40]
        stats = calculate_latency_stats(latencies)
        assert stats["median"] == 25.0

    def test_empty_list(self):
        """Empty list returns zeros."""
        stats = calculate_latency_stats([])
        assert stats["count"] == 0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["median"] == 0.0
        assert stats["mean"] == 0.0


class TestMcNemarTest:
    """Tests for McNemar's test implementation."""

    def test_perfect_agreement(self):
        """If predictions are identical, b=c=0 -> statistic=0 (or undefined)."""
        # pred: [1, 0, 1, 0], true: [1, 0, 1, 0]
        # Both correct or both incorrect everywhere.
        # Contingency:
        #       True
        #       +   -
        # P +  a    b
        #   -  c    d
        # Here: a=2 (both +), d=2 (both -), b=0, c=0.
        pred = [1, 0, 1, 0]
        baseline = [1, 0, 1, 0]
        # Expected: b=0, c=0.
        # The function should handle this gracefully (return 0 or nan).
        stat, pval = compute_mcnemar_test(pred, baseline)
        # If b+c == 0, stat is typically 0 or nan.
        # We assert it returns numbers without crashing.
        assert isinstance(stat, (int, float, type(None)))
        assert isinstance(pval, (int, float, type(None)))

    def test_disagreement(self):
        """Standard disagreement case."""
        # pred: [1, 1, 0, 0], baseline: [1, 0, 1, 0]
        # idx 0: 1,1 (a)
        # idx 1: 1,0 (b) -> pred+, base-
        # idx 2: 0,1 (c) -> pred-, base+
        # idx 3: 0,0 (d)
        # b=1, c=1.
        pred = [1, 1, 0, 0]
        baseline = [1, 0, 1, 0]
        stat, pval = compute_mcnemar_test(pred, baseline)
        # Chi-square approx: (|b-c|-1)^2 / (b+c) = (0)^2 / 2 = 0 (with continuity correction)
        # Without correction: (1-1)^2 / 2 = 0.
        # So stat should be 0.0.
        assert math.isclose(stat, 0.0, abs_tol=1e-6)
        assert pval is not None

    def test_significant_disagreement(self):
        """Case with significant difference."""
        # Large b, small c
        # b=10, c=1 -> (9-1)^2 / 11 = 64/11 ~ 5.8
        pred = [1] * 10 + [0] * 1 + [1] * 1 + [0] * 10
        baseline = [0] * 10 + [1] * 1 + [1] * 1 + [0] * 10
        # Wait, let's construct explicitly:
        # 10 cases where pred=1, base=0 (b)
        # 1 case where pred=0, base=1 (c)
        # 1 case where pred=1, base=1 (a)
        # 10 cases where pred=0, base=0 (d)
        pred = [1]*10 + [0] + [1] + [0]*10
        baseline = [0]*10 + [1] + [1] + [0]*10
        
        stat, pval = compute_mcnemar_test(pred, baseline)
        # b=10, c=1.
        # With continuity correction: (|9|-1)^2 / 11 = 64/11 = 5.81
        assert stat > 5.0


class TestLoaders:
    """Tests for data loading utilities."""

    def test_load_jsonl_string(self, tmp_path):
        """Load JSONL from a temporary file."""
        data_path = tmp_path / "test.jsonl"
        data_path.write_text('{"a": 1}\n{"a": 2}\n')
        
        result = load_jsonl(str(data_path))
        assert len(result) == 2
        assert result[0]["a"] == 1
        assert result[1]["a"] == 2

    def test_load_jsonl_missing_file(self, tmp_path):
        """Load JSONL from missing file returns empty list."""
        result = load_jsonl(str(tmp_path / "nonexistent.jsonl"))
        assert result == []

    def test_load_csv_simple(self, tmp_path):
        """Load CSV from a temporary file."""
        data_path = tmp_path / "test.csv"
        data_path.write_text("id,val\n1,a\n2,b\n")
        
        result = load_csv(str(data_path))
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[0]["val"] == "a"

    def test_load_csv_missing_file(self, tmp_path):
        """Load CSV from missing file returns empty list."""
        result = load_csv(str(tmp_path / "nonexistent.csv"))
        assert result == []