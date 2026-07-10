"""
Unit tests for memory projection logic in src/pipelines/ingest.py.
"""

import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Ensure src is in path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipelines.ingest import (
    estimate_peak_ram_gb,
    calculate_read_depth_stats,
    check_memory_and_subsample
)
from src.utils.memory import trigger_subsampling

class TestMemoryProjection:
    """Tests for memory estimation functions."""

    def test_estimate_peak_ram_gb_basic(self):
        """Test basic RAM estimation calculation."""
        # 100 samples * 20,000 reads * 150 bytes = 300,000,000 bytes
        # 300,000,000 / (1024^3) ≈ 0.279 GB
        result = estimate_peak_ram_gb(100, 20000, 150)
        expected = (100 * 20000 * 150) / (1024 ** 3)
        assert abs(result - expected) < 0.001

    def test_estimate_peak_ram_gb_large_dataset(self):
        """Test estimation for a large dataset that should exceed 6GB."""
        # 10,000 samples * 100,000 reads * 150 bytes
        # 15,000,000,000 bytes ≈ 13.97 GB
        result = estimate_peak_ram_gb(10000, 100000, 150)
        assert result > 6.0

    def test_calculate_read_depth_stats_missing_file(self):
        """Test handling of missing metadata file."""
        result = calculate_read_depth_stats("nonexistent_file.csv")
        assert result == (0, 0)

    def test_calculate_read_depth_stats_with_column(self):
        """Test calculation when read_count column exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("sample_id,read_count\ns1,1000\ns2,2000\ns3,3000\n")
            temp_path = f.name

        try:
            count, avg = calculate_read_depth_stats(temp_path)
            assert count == 3
            assert avg == 2000
        finally:
            os.unlink(temp_path)

    def test_calculate_read_depth_stats_no_column(self):
        """Test calculation when read_count column is missing (fallback)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("sample_id,biome\ns1,forest\ns2,grassland\n")
            temp_path = f.name

        try:
            count, avg = calculate_read_depth_stats(temp_path)
            assert count == 2
            # Default fallback is 25000
            assert avg == 25000
        finally:
            os.unlink(temp_path)

    def test_check_memory_and_subsample_under_limit(self):
        """Test that no subsampling is triggered when under limit."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("sample_id,read_count\ns1,1000\ns2,2000\n")
            temp_path = f.name

        try:
            triggered, peak_ram, msg = check_memory_and_subsample(
                temp_path,
                max_ram_gb=6.0,
                output_subsampled_path=None
            )
            assert triggered is False
            assert peak_ram < 6.0
            assert "MEMORY OK" in msg
        finally:
            os.unlink(temp_path)

    def test_check_memory_and_subsample_over_limit(self):
        """Test that subsampling is triggered when over limit."""
        # Create a file that simulates a large dataset
        # We need to trick the estimator into thinking it's large
        # We'll use a very high read count
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # 1000 samples * 1,000,000 reads -> ~139GB estimated
            f.write("sample_id,read_count\n")
            for i in range(1000):
                f.write(f"s{i},1000000\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "subsampled.csv")
                triggered, peak_ram, msg = check_memory_and_subsample(
                    temp_path,
                    max_ram_gb=6.0,
                    output_subsampled_path=output_path
                )
                assert triggered is True
                assert peak_ram > 6.0
                assert "MEMORY WARNING" in msg
                # Check if subsampling logic was called (file creation might depend on trigger_subsampling implementation)
                # For now, we just verify the trigger flag and log message
        finally:
            os.unlink(temp_path)
