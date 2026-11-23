import pytest
import numpy as np
from src.models.evaluate import benjamini_hochberg_correction

class TestBenjaminiHochbergCorrection:
    def test_empty_list(self):
        """Test with empty input."""
        rejections, adjusted = benjamini_hochberg_correction([])
        assert rejections == []
        assert adjusted == []

    def test_single_pvalue_reject(self):
        """Test with a single p-value that should be rejected."""
        rejections, adjusted = benjamini_hochberg_correction([0.01], alpha=0.05)
        assert len(rejections) == 1
        assert rejections[0] is True
        assert adjusted[0] <= 0.05

    def test_single_pvalue_fail(self):
        """Test with a single p-value that should not be rejected."""
        rejections, adjusted = benjamini_hochberg_correction([0.10], alpha=0.05)
        assert len(rejections) == 1
        assert rejections[0] is False
        assert adjusted[0] > 0.05

    def test_multiple_pvalues(self):
        """Test with multiple p-values."""
        p_vals = [0.01, 0.02, 0.03, 0.04, 0.10, 0.20]
        rejections, adjusted = benjamini_hochberg_correction(p_vals, alpha=0.05)
        
        # Check monotonicity of adjusted p-values
        for i in range(1, len(adjusted)):
            assert adjusted[i] >= adjusted[i-1], "Adjusted p-values must be monotonic"
        
        # Check that rejections correspond to adjusted <= alpha
        for i, rej in enumerate(rejections):
            if rej:
                assert adjusted[i] <= 0.05
            else:
                assert adjusted[i] > 0.05

    def test_all_reject(self):
        """Test case where all p-values are small."""
        p_vals = [0.001, 0.002, 0.003]
        rejections, adjusted = benjamini_hochberg_correction(p_vals, alpha=0.05)
        assert all(rejections)

    def test_none_reject(self):
        """Test case where all p-values are large."""
        p_vals = [0.2, 0.3, 0.4]
        rejections, adjusted = benjamini_hochberg_correction(p_vals, alpha=0.05)
        assert not any(rejections)