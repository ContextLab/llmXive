import pytest
import numpy as np
import json
import os
import tempfile
from pathlib import Path
import struct

# Import the functions to test
from code.analysis.stability_check import (
    calculate_l2_relative_error,
    calculate_max_absolute_difference,
    detect_nan_in_tensor,
    StabilityResult
)

class TestStabilityMetrics:
    def test_l2_relative_error_identical(self):
        """Test L2 error is 0 for identical tensors."""
        ref = [1.0, 2.0, 3.0]
        comp = [1.0, 2.0, 3.0]
        error = calculate_l2_relative_error(ref, comp)
        assert error == 0.0

    def test_l2_relative_error_nonzero(self):
        """Test L2 error calculation for different tensors."""
        ref = [1.0, 2.0, 3.0]
        comp = [1.0, 2.0, 4.0] # diff = 1 at last element
        # L2 diff = sqrt(1^2) = 1
        # L2 ref = sqrt(1+4+9) = sqrt(14)
        # Error = 1 / sqrt(14)
        expected = 1.0 / np.sqrt(14.0)
        error = calculate_l2_relative_error(ref, comp)
        assert np.isclose(error, expected)

    def test_l2_relative_error_zero_reference(self):
        """Test handling of zero reference norm."""
        ref = [0.0, 0.0, 0.0]
        comp = [1.0, 1.0, 1.0]
        error = calculate_l2_relative_error(ref, comp)
        assert error == float('inf')

    def test_max_absolute_difference(self):
        """Test Max Diff calculation."""
        ref = [1.0, 2.0, 3.0]
        comp = [1.1, 1.8, 3.5]
        # Diffs: |0.1|, |0.2|, |0.5| -> Max 0.5
        max_diff = calculate_max_absolute_difference(ref, comp)
        assert max_diff == 0.5

    def test_detect_nan_true(self):
        """Test NaN detection."""
        data = [1.0, float('nan'), 3.0]
        assert detect_nan_in_tensor(data, (3,)) is True

    def test_detect_nan_false(self):
        """Test no NaN detection."""
        data = [1.0, 2.0, 3.0]
        assert detect_nan_in_tensor(data, (3,)) is False

    def test_detect_inf_true(self):
        """Test Inf detection."""
        data = [1.0, float('inf'), 3.0]
        assert detect_nan_in_tensor(data, (3,)) is True