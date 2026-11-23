"""
Unit tests for aggregation utilities.
"""

import json
import tempfile
from pathlib import Path
import pytest

from analysis.aggregation_utils import aggregate_power_results


def test_aggregate_power_results_basic():
    """Test basic aggregation of simple results."""
    results = [
        {"sample_size": 10, "replication_success": True, "kernel_size": 4.0},
        {"sample_size": 10, "replication_success": False, "kernel_size": 4.0},
        {"sample_size": 20, "replication_success": True, "kernel_size": 4.0},
        {"sample_size": 20, "replication_success": True, "kernel_size": 4.0},
        {"sample_size": 20, "replication_success": False, "kernel_size": 8.0},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "power_curves.json"
        output = aggregate_power_results(results, out_path)

        assert output["sample_sizes_tested"] == [10, 20]
        assert output["empirical_rates"]["10"] == 0.5
        assert output["empirical_rates"]["20"] == 0.6667  # 2/3 rounded

        # Verify file exists and can be loaded
        with open(out_path) as f:
            loaded = json.load(f)
        assert loaded == output

def test_aggregate_power_results_empty():
    """Test that empty results raise ValueError."""
    with pytest.raises(ValueError):
        aggregate_power_results([], "dummy.json")

def test_aggregate_power_results_missing_sample_size():
    """Test handling of results with missing sample_size."""
    results = [
        {"sample_size": 10, "replication_success": True},
        {"replication_success": False},  # Missing sample_size
        {"sample_size": 10, "replication_success": False},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "power_curves.json"
        output = aggregate_power_results(results, out_path)

        # Should only have one entry for N=10
        assert output["sample_sizes_tested"] == [10]
        # 1 success out of 2 valid
        assert output["empirical_rates"]["10"] == 0.5

def test_aggregate_creates_directories():
    """Test that output path directories are created if missing."""
    results = [
        {"sample_size": 10, "replication_success": True, "kernel_size": 4.0},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Deeply nested path
        out_path = Path(tmpdir) / "level1" / "level2" / "power_curves.json"
        aggregate_power_results(results, out_path)

        assert out_path.exists()