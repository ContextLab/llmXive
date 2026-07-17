"""Unit tests for code/metrics.py"""
import pytest
from metrics import MetricsCalculator

def test_metrics_calculator_initialization():
    """Verify MetricsCalculator can be instantiated"""
    calc = MetricsCalculator()
    assert calc is not None

def test_metrics_calculator_has_methods():
    """Verify required methods exist"""
    calc = MetricsCalculator()
    assert hasattr(calc, "compute_sss")
    assert hasattr(calc, "compute_wer")
    assert hasattr(calc, "detect_collapse")
