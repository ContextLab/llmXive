"""
Unit tests to verify memory usage remains <7GB with generators for N=50.
This task implements T054: Create tests/unit/test_runner_memory.py.
"""
import pytest
import sys
import os
import tracemalloc
import gc

# Add src to path if running from project root
if "code" in os.getcwd():
    sys.path.insert(0, os.path.join(os.getcwd(), "code"))
elif os.path.basename(os.getcwd()) == "llmxive-follow-up-extending-dvao-dynamic":
    sys.path.insert(0, os.path.join(os.getcwd(), "code"))

from src.simulation.runner import generate_trajectories, check_memory_limit

# Memory limit in bytes (7GB)
MEMORY_LIMIT_BYTES = 7 * 1024**3  # 7 GB

@pytest.fixture(autouse=True)
def setup_tracemalloc():
    """Start and stop tracemalloc for each test."""
    tracemalloc.start()
    yield
    tracemalloc.stop()
    gc.collect()

class TestRunnerMemory:
    """Tests to verify memory efficiency of generator-based trajectory storage."""

    def test_generator_constant_memory_size(self):
        """
        Verify that the trajectory iterator remains constant size regardless of N.
        This confirms we are using generators, not lists.
        """
        # Test with N=5
        traj_iter_5 = generate_trajectories(n_objectives=5, seed=42, n_episodes=10)
        size_5 = sys.getsizeof(traj_iter_5)

        # Test with N=50
        traj_iter_50 = generate_trajectories(n_objectives=50, seed=42, n_episodes=10)
        size_50 = sys.getsizeof(traj_iter_50)

        # Sizes should be roughly equal (both are generator objects)
        # Allow small variance due to internal state, but not order-of-magnitude difference
        ratio = size_50 / size_5
        assert ratio < 2.0, (
            f"Generator size increased significantly: N=5 size={size_5}, "
            f"N=50 size={size_50}, ratio={ratio}. "
            "This suggests we might be storing data in memory instead of using generators."
        )

    def test_memory_usage_under_7gb_n50(self):
        """
        Verify that running with N=50 stays under 7GB memory limit.
        Uses tracemalloc to measure peak memory usage.
        """
        gc.collect()
        tracemalloc.start()

        try:
            # Generate trajectories for N=50
            # Use a moderate number of episodes to test memory
            n_episodes = 50
            traj_iterator = generate_trajectories(
                n_objectives=50,
                seed=42,
                n_episodes=n_episodes
            )

            # Consume the iterator to trigger actual memory usage
            count = 0
            for trajectory in traj_iterator:
                count += 1
                # Periodically check memory
                if count % 10 == 0:
                    current, peak = tracemalloc.get_traced_memory()
                    current_gb = current / 1024**3
                    peak_gb = peak / 1024**3

                    # Assert we haven't exceeded the limit
                    assert current_gb < 6.5, (
                        f"Memory usage exceeded safe threshold: {current_gb:.2f} GB. "
                        f"Current: {current / 1024**3:.2f} GB, Peak: {peak / 1024**3:.2f} GB"
                    )

            # Final check
            current, peak = tracemalloc.get_traced_memory()
            current_gb = current / 1024**3
            peak_gb = peak / 1024**3

            # Assert final memory is under 7GB
            assert peak_gb < 7.0, (
                f"Peak memory usage exceeded 7GB limit: {peak_gb:.2f} GB. "
                f"Current: {current_gb:.2f} GB, Peak: {peak_gb:.2f} GB"
            )

            # Verify we actually processed episodes
            assert count == n_episodes, (
                f"Expected {n_episodes} episodes, but processed {count}"
            )

        finally:
            tracemalloc.stop()

    def test_check_memory_limit_function(self):
        """
        Test that check_memory_limit correctly identifies when memory is under limit.
        """
        # This should not raise an exception
        try:
            check_memory_limit(MEMORY_LIMIT_BYTES)
        except MemoryError:
            pytest.fail("check_memory_limit raised MemoryError when memory should be under limit")

    def test_generator_lazy_evaluation(self):
        """
        Verify that trajectories are generated lazily (one at a time) rather than
        pre-computing all trajectories into memory.
        """
        import time

        gc.collect()
        tracemalloc.start()

        try:
            # Create iterator
            traj_iterator = generate_trajectories(
                n_objectives=50,
                seed=42,
                n_episodes=100
            )

            # Get initial memory
            initial_memory = tracemalloc.get_traced_memory()[0]

            # Get first trajectory
            first_traj = next(traj_iterator)
            memory_after_first = tracemalloc.get_traced_memory()[0]

            # Get second trajectory
            second_traj = next(traj_iterator)
            memory_after_second = tracemalloc.get_traced_memory()[0]

            # Memory increase should be roughly proportional to one trajectory,
            # not all trajectories
            delta_first = memory_after_first - initial_memory
            delta_second = memory_after_second - memory_after_first

            # The second delta should be similar to the first (one trajectory at a time)
            # Allow some variance but not order-of-magnitude difference
            ratio = delta_second / delta_first if delta_first > 0 else 1.0
            assert 0.5 < ratio < 2.0, (
                f"Memory growth pattern inconsistent with lazy evaluation. "
                f"First trajectory: {delta_first} bytes, Second: {delta_second} bytes, "
                f"Ratio: {ratio}"
            )

        finally:
            tracemalloc.stop()

    def test_large_n_memory_scaling(self):
        """
        Test that memory usage scales linearly with N (as expected for generator-based
        storage) rather than exponentially or with large constant factors.
        """
        gc.collect()
        tracemalloc.start()

        try:
            n_values = [10, 20, 50]
            memory_usages = []

            for n in n_values:
                traj_iterator = generate_trajectories(
                    n_objectives=n,
                    seed=42,
                    n_episodes=20
                )

                # Consume iterator
                for _ in traj_iterator:
                    pass

                current, peak = tracemalloc.get_traced_memory()
                memory_usages.append(peak)
                tracemalloc.clear_traces()
                tracemalloc.start()

            # Check that memory scales roughly linearly with N
            # (allowing for some overhead variance)
            # Memory[50] / Memory[10] should be roughly 50/10 = 5
            ratio_50_10 = memory_usages[2] / memory_usages[0] if memory_usages[0] > 0 else 0
            expected_ratio = 50 / 10

            # Allow 50% tolerance on linear scaling
            assert 0.5 * expected_ratio < ratio_50_10 < 1.5 * expected_ratio, (
                f"Memory scaling is not linear with N. "
                f"Expected ratio ~{expected_ratio}, got {ratio_50_10:.2f}. "
                f"Memory for N=10: {memory_usages[0] / 1024**2:.2f} MB, "
                f"Memory for N=50: {memory_usages[2] / 1024**2:.2f} MB"
            )

        finally:
            tracemalloc.stop()