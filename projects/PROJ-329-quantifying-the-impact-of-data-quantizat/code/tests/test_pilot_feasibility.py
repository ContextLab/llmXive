"""
Tests for pilot feasibility verification (T010).

Validates that batch size calculations and resource estimates are correct.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.verify_pilot_feasibility import (
    estimate_memory_per_signal,
    estimate_runtime_per_signal,
    calculate_batch_metrics,
    main
)
from src.config import get_resource_limits, calculate_batch_constraints


class TestMemoryEstimation:
    """Test memory estimation functions."""

    def test_memory_per_signal_positive(self):
        """Memory per signal should be positive."""
        mem = estimate_memory_per_signal()
        assert mem > 0, "Memory per signal must be positive"

    def test_memory_per_signal_reasonable(self):
        """Memory per signal should be < 1 GB (conservative estimate)."""
        mem = estimate_memory_per_signal()
        assert mem < 1.0, f"Memory per signal {mem} GB seems too high"

    def test_memory_scales_with_samples(self):
        """Memory should increase with number of samples."""
        mem_1024 = estimate_memory_per_signal(num_samples=1024)
        mem_4096 = estimate_memory_per_signal(num_samples=4096)
        assert mem_4096 > mem_1024, "Memory should increase with samples"


class TestRuntimeEstimation:
    """Test runtime estimation functions."""

    def test_runtime_per_signal_positive(self):
        """Runtime per signal should be positive."""
        runtime = estimate_runtime_per_signal()
        assert runtime > 0, "Runtime per signal must be positive"

    def test_runtime_increases_for_low_snr(self):
        """Runtime should be higher for lower SNR signals."""
        runtime_high_snr = estimate_runtime_per_signal(target_snr=40)
        runtime_low_snr = estimate_runtime_per_signal(target_snr=10)
        assert runtime_low_snr > runtime_high_snr, "Low SNR should take longer"

    def test_runtime_reasonable_range(self):
        """Runtime should be in reasonable range (seconds to minutes)."""
        runtime = estimate_runtime_per_signal()
        assert 10 < runtime < 600, f"Runtime {runtime}s seems unrealistic"


class TestBatchMetrics:
    """Test batch metrics calculation."""

    def test_total_signals_calculation(self):
        """Verify total signals = 6 depths × 4 bins × 50 signals."""
        metrics = calculate_batch_metrics()
        expected = 6 * 4 * 50  # 1200
        assert metrics['total_signals'] == expected, \
            f"Expected {expected} signals, got {metrics['total_signals']}"

    def test_memory_within_limit(self):
        """Total memory should be under 7 GB."""
        metrics = calculate_batch_metrics()
        assert metrics['total_memory_gb'] < 7.0, \
            f"Total memory {metrics['total_memory_gb']} GB exceeds 7 GB limit"

    def test_time_within_limit(self):
        """Parallel time should be under 6 hours."""
        metrics = calculate_batch_metrics()
        assert metrics['parallel_time_hours'] < 6.0, \
            f"Parallel time {metrics['parallel_time_hours']}h exceeds 6h limit"

    def test_feasibility_flag(self):
        """Feasibility flag should be True for valid configuration."""
        metrics = calculate_batch_metrics()
        assert metrics['feasible'] is True, "Pilot batch should be feasible"

    def test_depths_and_bins_correct(self):
        """Verify correct bit depths and SNR bins."""
        metrics = calculate_batch_metrics()
        expected_depths = [1, 8, 10, 12, 14, 16]
        expected_bins = [(8, 14), (14, 20), (20, 30), (30, 50)]
        
        assert metrics['depths'] == expected_depths, "Bit depths mismatch"
        assert metrics['snr_bins'] == expected_bins, "SNR bins mismatch"


class TestConfigIntegration:
    """Test integration with config module (T009)."""

    def test_resource_limits_exist(self):
        """Resource limits should be retrievable."""
        limits = get_resource_limits()
        assert 'max_memory_gb' in limits
        assert 'max_time_hours' in limits
        assert 'cores' in limits

    def test_batch_constraints_exist(self):
        """Batch constraints should be calculable."""
        constraints = calculate_batch_constraints()
        assert isinstance(constraints, dict)
        assert 'total_signals' in constraints

    def test_limits_match_constraints(self):
        """Limits should be consistent with constraints."""
        limits = get_resource_limits()
        metrics = calculate_batch_metrics()
        
        assert metrics['total_memory_gb'] < limits['max_memory_gb']
        assert metrics['parallel_time_hours'] < limits['max_time_hours']


class TestMainExecution:
    """Test main function execution."""

    def test_main_returns_success(self):
        """Main should return 0 on success."""
        # Note: This might write to disk, so we run in a temp dir if needed
        # For now, just verify it doesn't crash
        try:
            result = main()
            assert result == 0, "Main should return 0 on success"
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"Main exited with code {e.code}")

    def test_output_file_created(self):
        """Output file should be created in data/results/."""
        # Run main and check for file
        main()
        
        output_file = project_root / "data" / "results" / "pilot_feasibility.json"
        assert output_file.exists(), "Output file should be created"
        
        # Verify JSON is valid
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'task_id' in data
        assert data['task_id'] == 'T010'
        assert 'verification_passed' in data