import pytest
import json
import tempfile
import os
from pathlib import Path
import struct
import numpy as np

# Import the module under test
# Assuming the module is in code/analysis/stability_check.py
# We need to add code to path if not already done
import sys
sys.path.insert(0, 'code')

from analysis.stability_check import process_stability, StabilityResult, calculate_l2_relative_error, calculate_max_absolute_difference
from analysis.stability_metrics_generator import aggregate_stability_metrics

def create_dummy_tensor_file(path: Path, values: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(struct.pack('f' * len(values), *values))

def test_threshold_flagging():
    """Test that errors > 1e-5 are flagged as unstable and excluded from stable list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        log_dir = tmpdir / "logs"
        ref_dir = tmpdir / "refs"
        log_dir.mkdir()
        ref_dir.mkdir()

        # Create a reference tensor
        ref_values = [1.0, 2.0, 3.0, 4.0]
        ref_path = ref_dir / "ref.bin"
        create_dummy_tensor_file(ref_path, ref_values)

        # Create a log with a stable result (error < 1e-5)
        stable_log = {
            "config_id": "stable_config",
            "kernel_type": "matmul",
            "output_tensor": [1.000001, 2.000001, 3.000001, 4.000001], # Very small error
            "reference_tensor_path": str(ref_path),
            "source_file": "test.jsonl"
        }

        # Create a log with an unstable result (error > 1e-5)
        unstable_log = {
            "config_id": "unstable_config",
            "kernel_type": "matmul",
            "output_tensor": [1.0, 2.0, 3.0, 100.0], # Large error
            "reference_tensor_path": str(ref_path),
            "source_file": "test.jsonl"
        }

        logs = [stable_log, unstable_log]

        # Process stability
        stable_results, unstable_results = process_stability(logs, ref_dir, threshold=1e-5)

        assert len(stable_results) == 1
        assert stable_results[0].config_id == "stable_config"
        assert stable_results[0].status == "stable"
        assert not stable_results[0].threshold_exceeded

        assert len(unstable_results) == 1
        assert unstable_results[0].config_id == "unstable_config"
        assert unstable_results[0].status == "unstable"
        assert unstable_results[0].threshold_exceeded

def test_nan_detection_exclusion():
    """Test that NaNs are detected and excluded from both stable and unstable lists (recorded separately)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        log_dir = tmpdir / "logs"
        ref_dir = tmpdir / "refs"
        log_dir.mkdir()
        ref_dir.mkdir()

        ref_values = [1.0, 2.0, 3.0, 4.0]
        ref_path = ref_dir / "ref.bin"
        create_dummy_tensor_file(ref_path, ref_values)

        nan_log = {
            "config_id": "nan_config",
            "kernel_type": "softmax",
            "output_tensor": [1.0, float('nan'), 3.0, 4.0],
            "reference_tensor_path": str(ref_path),
            "source_file": "test.jsonl"
        }

        logs = [nan_log]
        stable_results, unstable_results = process_stability(logs, ref_dir, threshold=1e-5)

        # NaNs are usually captured in unstable_results with status 'nan_detected'
        # The function returns (stable, unstable). NaNs go to unstable.
        assert len(unstable_results) == 1
        assert unstable_results[0].status == "nan_detected"
        assert len(stable_results) == 0

def test_aggregation_excludes_unstable_from_stats():
    """Test that the aggregator produces a CSV where unstable rows have status='unstable'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        stable_in = tmpdir / "stable.jsonl"
        unstable_in = tmpdir / "unstable.jsonl"
        out_csv = tmpdir / "metrics.csv"

        # Write dummy stable
        with open(stable_in, 'w') as f:
            f.write(json.dumps({"config_id": "s1", "kernel_type": "matmul", "l2_error": 1e-6, "max_diff": 1e-6, "status": "stable", "threshold_exceeded": False, "raw_log_path": ""}) + '\n')

        # Write dummy unstable
        with open(unstable_in, 'w') as f:
            f.write(json.dumps({"config_id": "u1", "kernel_type": "matmul", "l2_error": 1e-2, "max_diff": 1e-2, "status": "unstable", "threshold_exceeded": True, "raw_log_path": ""}) + '\n')

        aggregate_stability_metrics(str(stable_in), str(unstable_in), str(out_csv))

        assert out_csv.exists()
        with open(out_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        statuses = {r['status'] for r in rows}
        assert 'stable' in statuses
        assert 'unstable' in statuses