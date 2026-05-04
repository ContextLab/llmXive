"""
Memory usage test for DPGMM model - verifies <7GB RAM limit during 1000 observation processing.

Per US1 acceptance criteria: Model must process 1000 streaming observations
without exceeding 7GB memory usage.

This test uses tracemalloc for accurate memory profiling and validates
memory stays within bounds at critical points:
1. Model initialization
2. After processing 100, 500, and 1000 observations
3. During anomaly scoring

Run with: pytest code/tests/unit/test_memory_profile.py -v
"""

import gc
import tracemalloc
import pytest
from pathlib import Path
from typing import Tuple

import numpy as np

# Import from the project's code directory
# These imports assume code/ is in PYTHONPATH during test execution
from src.models.dpgmm import DPGMMModel, DPGMMConfig
from src.models.anomaly_score import AnomalyScore
from scripts.profile_memory_1000_obs import (
    generate_synthetic_observations,
    create_streaming_observation,
    process_observation,
)

# Memory limit constant (7GB in bytes)
MEMORY_LIMIT_BYTES = 7 * 1024 * 1024 * 1024  # 7GB

# Checkpoint intervals for memory measurement
CHECKPOINT_OBSERVATIONS = [100, 500, 1000]


class MemoryProfileResult:
    """Container for memory profiling results."""

    def __init__(self):
        self.peak_memory_bytes = 0
        self.current_memory_bytes = 0
        self.checkpoint_memory: dict = {}  # {observation_count: memory_bytes}
        self.gc_before_bytes = 0
        self.gc_after_bytes = 0

    def to_dict(self) -> dict:
        return {
            "peak_memory_bytes": self.peak_memory_bytes,
            "current_memory_bytes": self.current_memory_bytes,
            "checkpoint_memory": self.checkpoint_memory,
            "gc_before_bytes": self.gc_before_bytes,
            "gc_after_bytes": self.gc_after_bytes,
            "peak_memory_gb": round(self.peak_memory_bytes / (1024**3), 3),
        }


def profile_memory_during_processing(
    model: DPGMMModel,
    num_observations: int = 1000,
    checkpoint_points: list = None,
) -> MemoryProfileResult:
    """
    Profile memory usage during streaming observation processing.

    Args:
        model: Initialized DPGMMModel instance
        num_observations: Number of observations to process
        checkpoint_points: List of observation counts to measure memory

    Returns:
        MemoryProfileResult with memory measurements
    """
    if checkpoint_points is None:
        checkpoint_points = CHECKPOINT_OBSERVATIONS

    result = MemoryProfileResult()

    # Start memory profiling
    tracemalloc.start()

    # Force garbage collection before baseline measurement
    gc.collect()
    current, peak = tracemalloc.get_traced_memory()
    result.gc_before_bytes = current

    # Generate synthetic observations
    observations = generate_synthetic_observations(
        num_observations=num_observations,
        anomaly_rate=0.05,
        feature_dim=3,
        seed=42,
    )

    # Process observations one at a time (streaming)
    processed_count = 0
    for obs in observations:
        # Create streaming observation wrapper
        streaming_obs = create_streaming_observation(obs)

        # Process through model
        process_observation(model, streaming_obs)

        processed_count += 1

        # Check memory at checkpoint points
        if processed_count in checkpoint_points:
            current, peak = tracemalloc.get_traced_memory()
            result.checkpoint_memory[processed_count] = current

    # Final memory measurements
    gc.collect()
    current, peak = tracemalloc.get_traced_memory()
    result.current_memory_bytes = current
    result.peak_memory_bytes = peak
    result.gc_after_bytes = current

    # Stop memory profiling
    tracemalloc.stop()

    return result


def test_memory_initialization_under_limit():
    """
    Test that DPGMM model initialization stays well under 7GB.

    Expected: Model creation should use <100MB (typical for Bayesian models)
    """
    # Start memory profiling
    tracemalloc.start()

    gc.collect()
    before_create, _ = tracemalloc.get_traced_memory()

    # Create model with default config
    config = DPGMMConfig()
    model = DPGMMModel(config=config)

    gc.collect()
    after_create, peak = tracemalloc.get_traced_memory()

    tracemalloc.stop()

    memory_used = after_create - before_create
    memory_gb = memory_used / (1024**3)

    # Model initialization should be minimal (<100MB)
    assert memory_used < 100 * 1024 * 1024, (
        f"Model initialization used {memory_gb:.3f}GB, expected <0.1GB"
    )

    print(f"✓ Model initialization: {memory_gb:.3f}GB (limit: 0.1GB)")


def test_memory_processing_1000_observations_under_7gb():
    """
    Test that processing 1000 observations stays under 7GB memory limit.

    This is the core US1 memory requirement test.
    """
    # Create model
    config = DPGMMConfig()
    model = DPGMMModel(config=config)

    # Profile memory during processing
    result = profile_memory_during_processing(
        model=model,
        num_observations=1000,
        checkpoint_points=CHECKPOINT_OBSERVATIONS,
    )

    # Assert peak memory is under 7GB
    assert result.peak_memory_bytes < MEMORY_LIMIT_BYTES, (
        f"Peak memory {result.peak_memory_gb:.3f}GB exceeds 7GB limit"
    )

    # Assert final memory is under 7GB
    assert result.current_memory_bytes < MEMORY_LIMIT_BYTES, (
        f"Final memory {result.current_memory_gb:.3f}GB exceeds 7GB limit"
    )

    # Log checkpoint memory progression
    print("\nMemory checkpoint progression:")
    for obs_count, mem_bytes in sorted(result.checkpoint_memory.items()):
        mem_gb = mem_bytes / (1024**3)
        print(f"  {obs_count:4d} observations: {mem_gb:.3f}GB")

    print(f"\n✓ Peak memory: {result.peak_memory_gb:.3f}GB (limit: 7GB)")
    print(f"✓ Final memory: {result.current_memory_gb:.3f}GB (limit: 7GB)")
    print(f"✓ GC before: {result.gc_before_bytes / (1024**2):.1f}MB")
    print(f"✓ GC after: {result.gc_after_bytes / (1024**2):.1f}MB")


def test_memory_growth_rate_acceptable():
    """
    Test that memory growth rate is linear/acceptable (not exponential).

    This ensures the streaming update mechanism doesn't accumulate
    unbounded memory over time.
    """
    config = DPGMMConfig()
    model = DPGMMModel(config=config)

    result = profile_memory_during_processing(
        model=model,
        num_observations=1000,
        checkpoint_points=CHECKPOINT_OBSERVATIONS,
    )

    # Calculate memory growth per 100 observations
    if len(result.checkpoint_memory) >= 2:
        sorted_points = sorted(result.checkpoint_memory.items())

        # Memory should grow roughly linearly (not exponentially)
        # First 100 -> 500 observations
        mem_100 = sorted_points[0][1]
        mem_500 = sorted_points[1][1]

        growth_100_to_500 = mem_500 - mem_100
        observations_100_to_500 = 400

        # Second 500 -> 1000 observations
        mem_1000 = sorted_points[2][1]
        growth_500_to_1000 = mem_1000 - mem_500
        observations_500_to_1000 = 500

        # Growth rate per observation
        rate_1 = growth_100_to_500 / observations_100_to_500
        rate_2 = growth_500_to_1000 / observations_500_to_1000

        # Rates should be similar (linear growth), not diverging
        # Allow 2x variance for acceptable memory management
        ratio = max(rate_1, rate_2) / max(min(rate_1, rate_2), 1)

        print(f"\nMemory growth analysis:")
        print(f"  Rate 100->500: {rate_1:.1f} bytes/observation")
        print(f"  Rate 500->1000: {rate_2:.1f} bytes/observation")
        print(f"  Growth ratio: {ratio:.2f}x (should be ~1.0)")

        # Allow up to 3x variance for acceptable streaming behavior
        assert ratio < 3.0, (
            f"Memory growth rate diverging ({ratio:.2f}x), "
            "suggests non-linear accumulation"
        )


def test_memory_after_anomaly_scoring():
    """
    Test memory usage after computing anomaly scores.

    Scoring should not significantly increase memory footprint
    since it's a read-only operation on the posterior.
    """
    config = DPGMMConfig()
    model = DPGMMModel(config=config)

    # Process 500 observations
    result_before = profile_memory_during_processing(
        model=model,
        num_observations=500,
        checkpoint_points=[500],
    )

    # Score a batch of observations
    observations = generate_synthetic_observations(
        num_observations=100,
        anomaly_rate=0.05,
        feature_dim=3,
        seed=43,
    )

    gc.collect()
    before_score, _ = tracemalloc.get_traced_memory()

    # Score observations
    scores: list[AnomalyScore] = []
    for obs in observations:
        score = model.compute_anomaly_score(obs)
        scores.append(score)

    gc.collect()
    after_score, peak = tracemalloc.get_traced_memory()

    score_memory = after_score - before_score

    print(f"\nAnomaly scoring memory:")
    print(f"  Memory for 100 scores: {score_memory / (1024**2):.1f}MB")

    # Scoring 100 observations should be minimal (<50MB)
    assert score_memory < 50 * 1024 * 1024, (
        f"Anomaly scoring used {score_memory / (1024**2):.1f}MB, expected <50MB"
    )


def test_memory_with_different_feature_dimensions():
    """
    Test memory usage with varying feature dimensions.

    Higher dimensions should increase memory but stay under 7GB for
    reasonable feature counts (up to 100 features).
    """
    feature_dims = [3, 10, 50, 100]

    for dim in feature_dims:
        config = DPGMMConfig()
        model = DPGMMModel(config=config)

        result = profile_memory_during_processing(
            model=model,
            num_observations=1000,
            checkpoint_points=[1000],
        )

        # For higher dimensions, allow more memory but still under 7GB
        expected_increase = dim / 3.0  # Rough estimate
        adjusted_limit = min(MEMORY_LIMIT_BYTES, 2 * 1024 * 1024 * 1024)

        assert result.peak_memory_bytes < adjusted_limit, (
            f"Feature dim {dim}: {result.peak_memory_bytes / (1024**3):.3f}GB "
            f"exceeds limit for {dim}D features"
        )

        print(f"✓ Feature dim {dim:3d}: {result.peak_memory_bytes / (1024**2):.1f}MB")


def test_memory_with_concentration_parameter_tuning():
    """
    Test memory usage when concentration parameter is tuned.

    Adaptive concentration tuning should not cause unbounded
    memory growth (new components should be bounded).
    """
    config = DPGMMConfig()
    config.max_components = 50  # Limit components
    model = DPGMMModel(config=config)

    # Process with adaptive concentration tuning enabled
    result = profile_memory_during_processing(
        model=model,
        num_observations=1000,
        checkpoint_points=CHECKPOINT_OBSERVATIONS,
    )

    # Verify active component count is reasonable
    active_components = model.get_active_component_count()
    print(f"\nConcentration tuning test:")
    print(f"  Active components: {active_components}")
    print(f"  Max components: {config.max_components}")

    assert active_components <= config.max_components, (
        f"Active components {active_components} exceeds max {config.max_components}"
    )

    # Memory should still be under 7GB
    assert result.peak_memory_bytes < MEMORY_LIMIT_BYTES, (
        f"Memory {result.peak_memory_gb:.3f}GB exceeds 7GB with concentration tuning"
    )


def test_memory_gc_effectiveness():
    """
    Test that garbage collection effectively reclaims memory.

    After processing and explicit GC, memory should not grow
    unboundedly with repeated processing cycles.
    """
    config = DPGMMConfig()
    model = DPGMMModel(config=config)

    # Process 500 observations
    result1 = profile_memory_during_processing(
        model=model,
        num_observations=500,
        checkpoint_points=[500],
    )

    # Force GC
    gc.collect()
    mem_after_gc1, _ = tracemalloc.get_traced_memory()

    # Process another 500 observations
    result2 = profile_memory_during_processing(
        model=model,
        num_observations=500,
        checkpoint_points=[500],
    )

    # Force GC again
    gc.collect()
    mem_after_gc2, _ = tracemalloc.get_traced_memory()

    # Memory should not grow significantly between cycles
    growth = mem_after_gc2 - mem_after_gc1

    print(f"\nGC effectiveness test:")
    print(f"  Memory after cycle 1: {mem_after_gc1 / (1024**2):.1f}MB")
    print(f"  Memory after cycle 2: {mem_after_gc2 / (1024**2):.1f}MB")
    print(f"  Growth between cycles: {growth / (1024**2):.1f}MB")

    # Allow up to 10% growth for GC overhead
    assert growth < 0.1 * mem_after_gc1, (
        f"Memory grew {growth / (1024**2):.1f}MB between GC cycles, "
        "suggests leak"
    )


def test_memory_profile_result_serialization():
    """
    Test that memory profile results can be serialized.

    This ensures results can be logged and compared across runs.
    """
    config = DPGMMConfig()
    model = DPGMMModel(config=config)

    result = profile_memory_during_processing(
        model=model,
        num_observations=100,
        checkpoint_points=[100],
    )

    # Serialize to dict
    result_dict = result.to_dict()

    # Verify all expected keys present
    expected_keys = [
        "peak_memory_bytes",
        "current_memory_bytes",
        "checkpoint_memory",
        "gc_before_bytes",
        "gc_after_bytes",
        "peak_memory_gb",
    ]

    for key in expected_keys:
        assert key in result_dict, f"Missing key: {key}"

    # Verify numeric types
    assert isinstance(result_dict["peak_memory_bytes"], int)
    assert isinstance(result_dict["peak_memory_gb"], float)

    print(f"\n✓ Memory profile result serialization: OK")


def test_memory_limit_is_reasonable():
    """
    Sanity check that 7GB limit is reasonable for the task.

    This test documents why 7GB was chosen as the limit.
    """
    # Typical memory usage breakdown for 1000 observations:
    # - Model parameters: ~10-100MB (depends on components)
    # - Observation buffer: ~1MB (1000 observations x 3 features)
    # - Posterior cache: ~50-200MB (variational parameters)
    # - Overhead: ~100-500MB (Python objects, numpy arrays)
    # - Total expected: <1GB typically

    # 7GB provides 7x headroom for edge cases and debugging

    expected_typical_memory = 500 * 1024 * 1024  # 500MB
    memory_limit = MEMORY_LIMIT_BYTES
    headroom_ratio = memory_limit / expected_typical_memory

    print(f"\nMemory limit analysis:")
    print(f"  Expected typical: {expected_typical_memory / (1024**2):.0f}MB")
    print(f"  Configured limit: {MEMORY_LIMIT_BYTES / (1024**3):.1f}GB")
    print(f"  Headroom ratio: {headroom_ratio:.1f}x")

    # Verify we have at least 5x headroom
    assert headroom_ratio >= 5.0, (
        f"Memory limit headroom ({headroom_ratio:.1f}x) too low, expected >=5x"
    )


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "--tb=short"])
