"""
Unit tests for metrics calculations in code/metrics.py.

Tests SSS, WER, baseline computation, and collapse detection.
"""
import pytest
import json
import math
from pathlib import Path

from metrics import MetricsCalculator, compute_baseline_sss_and_wer


class TestMetricsCalculator:
    """Tests for MetricsCalculator class."""

    def test_create_calculator(self):
        """Test creating a MetricsCalculator instance."""
        # Note: Actual initialization may require model loading
        # We test the structure here
        calculator = MetricsCalculator()
        assert calculator is not None

    def test_compute_wer(self):
        """Test WER computation."""
        calculator = MetricsCalculator()
        
        # Perfect match
        wer = calculator.compute_wer("hello world", "hello world")
        assert wer == 0.0

        # Complete mismatch
        wer = calculator.compute_wer("hello world", "goodbye universe")
        assert wer > 0.0
        assert wer <= 1.0

    def test_compute_sss(self):
        """Test Semantic Similarity Score computation."""
        calculator = MetricsCalculator()
        
        # Similar sentences should have high SSS
        sss = calculator.compute_sss("The cat sat on the mat", "A cat is sitting on a mat")
        assert 0.0 <= sss <= 1.0

    def test_normalize_sss(self):
        """Test SSS normalization against baseline."""
        calculator = MetricsCalculator()
        
        baseline_sss = 0.9
        raw_sss = 0.45
        normalized = calculator.normalize_sss(raw_sss, baseline_sss)
        
        expected = raw_sss / baseline_sss
        assert abs(normalized - expected) < 1e-6

    def test_check_collapse(self):
        """Test collapse detection logic."""
        calculator = MetricsCalculator()
        
        # Test with SSS below threshold and WER spike
        is_collapse = calculator.check_collapse(
            normalized_sss=0.4,
            baseline_sss=0.9,
            wer=0.6,
            baseline_wer=0.1,
            sss_threshold=0.5,
            wer_multiplier=2.0
        )
        assert is_collapse is True

        # Test with SSS above threshold
        is_collapse = calculator.check_collapse(
            normalized_sss=0.6,
            baseline_sss=0.9,
            wer=0.6,
            baseline_wer=0.1,
            sss_threshold=0.5,
            wer_multiplier=2.0
        )
        assert is_collapse is False

        # Test with WER below spike threshold
        is_collapse = calculator.check_collapse(
            normalized_sss=0.4,
            baseline_sss=0.9,
            wer=0.15,
            baseline_wer=0.1,
            sss_threshold=0.5,
            wer_multiplier=2.0
        )
        assert is_collapse is False


class TestComputeBaseline:
    """Tests for compute_baseline_sss_and_wer function."""

    def test_compute_baseline_empty_list(self):
        """Test baseline computation with empty list."""
        results = []
        baseline_sss, baseline_wer = compute_baseline_sss_and_wer(results)
        
        assert baseline_sss == 0.0
        assert baseline_wer == 0.0

    def test_compute_baseline_single_item(self):
        """Test baseline computation with single item."""
        results = [
            {"sss": 0.9, "wer": 0.05}
        ]
        baseline_sss, baseline_wer = compute_baseline_sss_and_wer(results)
        
        assert baseline_sss == 0.9
        assert baseline_wer == 0.05

    def test_compute_baseline_multiple_items(self):
        """Test baseline computation with multiple items."""
        results = [
            {"sss": 0.9, "wer": 0.05},
            {"sss": 0.85, "wer": 0.08},
            {"sss": 0.95, "wer": 0.04}
        ]
        baseline_sss, baseline_wer = compute_baseline_sss_and_wer(results)
        
        expected_sss = (0.9 + 0.85 + 0.95) / 3
        expected_wer = (0.05 + 0.08 + 0.04) / 3
        
        assert abs(baseline_sss - expected_sss) < 1e-6
        assert abs(baseline_wer - expected_wer) < 1e-6
