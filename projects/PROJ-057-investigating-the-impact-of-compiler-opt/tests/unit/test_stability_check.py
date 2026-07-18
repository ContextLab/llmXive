import pytest
import numpy as np
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.stability_check import (
    detect_nan_in_tensor,
    calculate_l2_relative_error,
    calculate_max_absolute_difference,
    StabilityResult,
    process_stability,
    load_raw_logs
)

class TestNaNDetection:
    def test_detect_nan_true(self):
        data = [1.0, np.nan, 3.0]
        assert detect_nan_in_tensor(data) is True

    def test_detect_nan_false(self):
        data = [1.0, 2.0, 3.0]
        assert detect_nan_in_tensor(data) is False

    def test_detect_nan_empty(self):
        assert detect_nan_in_tensor([]) is False

    def test_detect_nan_none(self):
        assert detect_nan_in_tensor(None) is False

class TestErrorCalculations:
    def test_l2_relative_error_zero(self):
        p = [1.0, 2.0, 3.0]
        r = [1.0, 2.0, 3.0]
        assert calculate_l2_relative_error(p, r) == 0.0

    def test_l2_relative_error_nonzero(self):
        p = [2.0, 2.0, 3.0]
        r = [1.0, 2.0, 3.0]
        # Diff: [1, 0, 0], L2_diff = 1
        # Ref: [1, 2, 3], L2_ref = sqrt(1+4+9) = sqrt(14)
        expected = 1.0 / np.sqrt(14)
        assert abs(calculate_l2_relative_error(p, r) - expected) < 1e-9

    def test_max_diff(self):
        p = [1.0, 5.0, 3.0]
        r = [1.0, 2.0, 3.0]
        # Diff: [0, 3, 0] -> Max 3
        assert calculate_max_absolute_difference(p, r) == 3.0

class TestProcessStability:
    def test_process_nan_exclusion(self):
        logs = [
            {"config_id": "c1", "kernel": "matmul", "output_tensor": [1.0, np.nan, 3.0]},
            {"config_id": "c2", "kernel": "matmul", "output_tensor": [1.0, 2.0, 3.0]}
        ]
        results = process_stability(logs)
        
        assert len(results) == 2
        assert results[0].status == "unstable_nan"
        assert results[0].has_nan is True
        assert results[1].status == "stable" # No reference provided, so stable by default in this test
        assert results[1].has_nan is False

    def test_process_stable_with_reference(self):
        # Create a temporary reference file
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_path = Path(tmpdir) / "matmul_ref.npy"
            np.save(ref_path, np.array([1.0, 2.0, 3.0]))
            
            logs = [
                {"config_id": "c1", "kernel": "matmul", "output_tensor": [1.0, 2.0, 3.0]}, # Perfect match
                {"config_id": "c2", "kernel": "matmul", "output_tensor": [10.0, 20.0, 30.0]} # Large error
            ]
            
            results = process_stability(logs, reference_dir=tmpdir)
            
            # c1 should be stable
            assert results[0].status == "stable"
            # c2 should be unstable due to error
            assert results[1].status == "unstable_error"

class TestLoadRawLogs:
    def test_load_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.jsonl"
            data = {"config_id": "c1", "kernel": "matmul", "output_tensor": [1.0, 2.0]}
            with open(log_file, 'w') as f:
                f.write(json.dumps(data) + "\n")
            
            logs = load_raw_logs(tmpdir)
            assert len(logs) == 1
            assert logs[0]["config_id"] == "c1"