"""
Contract test asserting FDR <= 0.05 after Benjamini-Hochberg correction.
"""
import pytest

def test_fdr_threshold(corrected_fdr: float):
    """
    Assert False Discovery Rate <= 0.05.
    """
    if corrected_fdr is None:
        pytest.skip("FDR fixture not available.")

    assert corrected_fdr <= 0.05, f"FDR ({corrected_fdr}) exceeds threshold 0.05"
