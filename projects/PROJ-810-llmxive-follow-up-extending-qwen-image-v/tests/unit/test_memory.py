"""
Unit tests for memory budget estimation utilities.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.memory import (
    estimate_peak_ram_usage,
    calculate_max_samples,
    determine_chunk_size,
    estimate_runtime,
    run_runtime_fallback_logic
)


class TestMemoryUtils:
    """Test suite for memory estimation functions."""

    def test_estimate_peak_ram_usage_basic(self):
        """Test basic memory estimation for a small batch."""
        result = estimate_peak_ram_usage(n_samples=100)
        
        assert "peak_ram_gb" in result
        assert "model_memory_gb" in result
        assert "per_sample_memory_gb" in result
        assert "sample_memory_gb" in result
        assert result["n_samples"] == 100
        assert result["peak_ram_gb"] > 0
        assert result["model_memory_gb"] > 0

    def test_estimate_peak_ram_usage_scaling(self):
        """Test that memory scales linearly with sample count."""
        result_100 = estimate_peak_ram_usage(n_samples=100)
        result_200 = estimate_peak_ram_usage(n_samples=200)
        
        # Sample memory should scale linearly
        ratio = result_200["sample_memory_gb"] / result_100["sample_memory_gb"]
        assert abs(ratio - 2.0) < 0.1  # Allow small floating point errors

    def test_calculate_max_samples_positive(self):
        """Test max samples calculation with available RAM."""
        max_samples = calculate_max_samples(available_ram_gb=7.0)
        
        assert max_samples > 0
        assert isinstance(max_samples, int)

    def test_calculate_max_samples_zero_ram(self):
        """Test max samples calculation with zero available RAM."""
        max_samples = calculate_max_samples(available_ram_gb=0.0)
        
        assert max_samples == 0

    def test_determine_chunk_size_within_limit(self):
        """Test chunk size determination when max_samples >= target."""
        chunk_size = determine_chunk_size(max_samples=2000, target_max_samples=1000)
        
        assert chunk_size == 1000

    def test_determine_chunk_size_below_limit(self):
        """Test chunk size determination when max_samples < target."""
        chunk_size = determine_chunk_size(max_samples=500, target_max_samples=1000)
        
        assert chunk_size == 500

    def test_determine_chunk_size_zero_max(self):
        """Test chunk size determination with zero max_samples."""
        chunk_size = determine_chunk_size(max_samples=0, target_max_samples=1000)
        
        assert chunk_size == 1

    def test_estimate_runtime_basic(self):
        """Test basic runtime estimation."""
        result = estimate_runtime(n_samples=1000, samples_per_hour=500)
        
        assert "estimated_hours" in result
        assert "estimated_seconds" in result
        assert result["estimated_hours"] == 2.0
        assert result["estimated_seconds"] == 7200

    def test_run_runtime_fallback_logic_pass(self):
        """Test runtime fallback when within limits."""
        result = run_runtime_fallback_logic(n_required=1000, max_runtime_hours=6.0)
        
        assert result["status"] == "pass"
        assert result["n_fallback"] == 1000
        assert result["estimated_runtime_hours"] > 0

    def test_run_runtime_fallback_logic_inconclusive(self):
        """Test runtime fallback when exceeding limits."""
        # With 500 samples/hour, 5000 samples would take 10 hours
        result = run_runtime_fallback_logic(n_required=5000, max_runtime_hours=6.0)
        
        assert result["status"] == "runtime_inconclusive"
        assert result["n_fallback"] < result["n_required"]
        assert result["n_fallback"] <= 3000  # 6 hours * 500 samples/hour

    def test_run_runtime_fallback_logic_zero_required(self):
        """Test runtime fallback with zero required samples."""
        result = run_runtime_fallback_logic(n_required=0, max_runtime_hours=6.0)
        
        assert result["status"] == "pass"
        assert result["n_fallback"] == 0
