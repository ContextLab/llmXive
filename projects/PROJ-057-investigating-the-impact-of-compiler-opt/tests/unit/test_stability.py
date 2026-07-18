import pytest
import numpy as np
import json
import os
import sys
from pathlib import Path
from dataclasses import asdict

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.stability_check import (
    StabilityResult,
    detect_nan_in_tensor,
    calculate_l2_relative_error,
    calculate_max_absolute_difference,
    process_stability,
    STABILITY_THRESHOLD
)

class TestStabilityThresholdFlagging:
    """Tests for T022: Threshold flagging and exclusion logic."""

    def test_l2_error_below_threshold_is_stable(self):
        """Verify that L2 error < 1e-5 is marked as stable."""
        # Create mock log entries
        ref_tensor = [1.0] * 100
        # Output with very small error (1e-6)
        out_tensor = [1.0 + 1e-6 for _ in range(100)]
        
        logs = [{
            "config_id": "test_O2",
            "kernel_type": "matmul",
            "output_tensor": out_tensor,
            "reference_tensor": ref_tensor,
            "source_file": "test.jsonl"
        }]
        
        results = process_stability(logs)
        assert len(results) == 1
        assert results[0].status == "stable"
        assert results[0].l2_error < STABILITY_THRESHOLD

    def test_l2_error_above_threshold_is_unstable(self):
        """Verify that L2 error > 1e-5 is marked as unstable (stability failure)."""
        ref_tensor = [1.0] * 100
        # Output with significant error (1e-4)
        out_tensor = [1.0 + 1e-4 for _ in range(100)]
        
        logs = [{
            "config_id": "test_ffast",
            "kernel_type": "softmax",
            "output_tensor": out_tensor,
            "reference_tensor": ref_tensor,
            "source_file": "test.jsonl"
        }]
        
        results = process_stability(logs)
        assert len(results) == 1
        assert results[0].status == "unstable"
        assert results[0].l2_error > STABILITY_THRESHOLD

    def test_nan_detection_marks_unstable(self):
        """Verify that NaN in output tensor marks configuration as unstable."""
        ref_tensor = [1.0] * 100
        out_tensor = [1.0, float('nan'), 1.0] + [1.0] * 97
        
        logs = [{
            "config_id": "test_nan",
            "kernel_type": "layernorm",
            "output_tensor": out_tensor,
            "reference_tensor": ref_tensor,
            "source_file": "test.jsonl"
        }]
        
        results = process_stability(logs)
        assert len(results) == 1
        assert results[0].status == "unstable"
        assert results[0].is_nan_detected is True

    def test_exclusion_logic_separates_stable_unstable(self):
        """Verify that process_stability correctly separates stable vs unstable for downstream use."""
        ref_tensor = [1.0] * 100
        
        logs = [
            {
                "config_id": "stable_config",
                "kernel_type": "matmul",
                "output_tensor": [1.0 + 1e-6 for _ in range(100)],
                "reference_tensor": ref_tensor,
                "source_file": "test1.jsonl"
            },
            {
                "config_id": "unstable_config",
                "kernel_type": "matmul",
                "output_tensor": [1.0 + 1e-3 for _ in range(100)],
                "reference_tensor": ref_tensor,
                "source_file": "test2.jsonl"
            }
        ]
        
        results = process_stability(logs)
        
        stable_results = [r for r in results if r.status == "stable"]
        unstable_results = [r for r in results if r.status == "unstable"]
        
        assert len(stable_results) == 1
        assert stable_results[0].config_id == "stable_config"
        
        assert len(unstable_results) == 1
        assert unstable_results[0].config_id == "unstable_config"

    def test_max_diff_calculation(self):
        """Verify Maximum Absolute Difference calculation."""
        ref_tensor = [1.0, 2.0, 3.0]
        out_tensor = [1.1, 2.0, 2.9]
        
        max_diff = calculate_max_absolute_difference(out_tensor, ref_tensor)
        expected = 0.1
        
        assert abs(max_diff - expected) < 1e-6

    def test_l2_relative_error_calculation(self):
        """Verify L2 Relative Error calculation."""
        ref_tensor = [3.0, 4.0]  # L2 norm = 5
        out_tensor = [3.1, 4.0]  # Diff = [0.1, 0.0], L2 diff = 0.1
        
        l2_error = calculate_l2_relative_error(out_tensor, ref_tensor)
        expected = 0.1 / 5.0  # 0.02
        
        assert abs(l2_error - expected) < 1e-6