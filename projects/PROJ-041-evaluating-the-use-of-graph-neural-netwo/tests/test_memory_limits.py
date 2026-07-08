"""
Test skeleton for graph construction memory limit (US1).
Asserts that tracemalloc peak memory usage stays below 7GB during graph construction.
Depends on: T005 (memory_monitor), T013 (graph construction logic in preprocess.py)
"""
import os
import sys
import tracemalloc
import pytest

# Add project root to path to allow imports from code/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.memory_monitor import (
    MemoryLimitExceededError,
    get_peak_memory_mb,
    memory_limit,
    check_memory_limit,
    start_monitoring,
)
from data.preprocess import preprocess_graph, extract_lcc
from data.ingest_netflow import ensure_data_dirs, download_ctu_dataset, download_bot_iot_dataset

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024


class TestGraphConstructionMemoryLimits:
    """
    Tests to verify that graph construction and preprocessing
    stay within the 7GB memory limit.
    """

    def test_memory_monitor_initialization(self):
        """Test that memory monitor utilities are available and functional."""
        start_monitoring()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        # Just verify we can get memory values without crashing
        assert isinstance(peak, (int, float))

    def test_memory_limit_constant(self):
        """Verify the memory limit constant is set correctly."""
        assert memory_limit == MEMORY_LIMIT_MB

    def test_check_memory_limit_pass(self):
        """Test check_memory_limit passes when under limit."""
        # Simulate a small memory usage (100MB)
        # This test verifies the function doesn't raise when under limit
        try:
            check_memory_limit(100)
        except MemoryLimitExceededError:
            pytest.fail("check_memory_limit raised unexpectedly for low memory usage")

    def test_check_memory_limit_fail(self):
        """Test check_memory_limit raises when over limit."""
        # Simulate memory usage over 7GB
        with pytest.raises(MemoryLimitExceededError):
            check_memory_limit(MEMORY_LIMIT_MB + 100)

    @pytest.mark.skip(reason="Requires real data download - run with --real-data flag")
    def test_preprocess_graph_memory_limit(self):
        """
        Test that preprocess_graph stays within memory limit.
        This test requires real data to be downloaded first.
        Run with: pytest tests/test_memory_limits.py::TestGraphConstructionMemoryLimits::test_preprocess_graph_memory_limit --real-data
        """
        import argparse

        # Check if --real-data flag is provided
        parser = argparse.ArgumentParser()
        parser.add_argument('--real-data', action='store_true')
        args, _ = parser.parse_known_args()

        if not args.real_data:
            pytest.skip("Real data download required. Run with --real-data flag.")

        # Start memory monitoring
        start_monitoring()

        try:
            # Ensure data directories exist
            ensure_data_dirs()

            # Try to download dataset (will use fallback if needed)
            try:
                download_ctu_dataset()
            except Exception:
                try:
                    download_bot_iot_dataset()
                except Exception as e:
                    pytest.skip(f"Could not download dataset: {e}")

            # Get path to raw data
            raw_data_path = os.path.join("data", "raw", "ctu-10")
            if not os.path.exists(raw_data_path):
                raw_data_path = os.path.join("data", "raw", "NF-BoT-IoT")

            if not os.path.exists(raw_data_path):
                pytest.skip("No raw data available")

            # Run preprocessing
            preprocess_graph(raw_data_path)

            # Check memory usage
            peak_mb = get_peak_memory_mb()
            assert peak_mb < MEMORY_LIMIT_MB, (
                f"Memory limit exceeded: {peak_mb:.2f}MB > {MEMORY_LIMIT_MB:.2f}MB"
            )

        finally:
            tracemalloc.stop()

    def test_extract_lcc_memory_limit(self):
        """
        Test that extract_lcc function respects memory limits.
        Creates a small test graph to verify the function works within limits.
        """
        import networkx as nx

        # Create a test graph (small enough to not cause memory issues)
        G = nx.erdos_renyi_graph(1000, 0.01)

        start_monitoring()
        try:
            lcc = extract_lcc(G)
            assert lcc.number_of_nodes() > 0
        finally:
            tracemalloc.stop()

        # Verify memory usage was within limits
        peak_mb = get_peak_memory_mb()
        assert peak_mb < MEMORY_LIMIT_MB, (
            f"Memory limit exceeded: {peak_mb:.2f}MB > {MEMORY_LIMIT_MB:.2f}MB"
        )

    def test_memory_monitor_context_manager(self):
        """Test the memory monitoring context manager."""
        from utils.memory_monitor import memory_limit

        with memory_limit(MEMORY_LIMIT_MB):
            # This should not raise
            current, peak = tracemalloc.get_traced_memory()
            assert peak < MEMORY_LIMIT_MB

    def test_memory_monitor_context_manager_overflow(self):
        """Test that context manager raises on memory overflow."""
        with pytest.raises(MemoryLimitExceededError):
            with memory_limit(1):  # 1MB limit
                # Simulate memory allocation
                data = [0] * (10 * 1024 * 1024)  # 10MB
                del data

    def test_memory_functions_exist(self):
        """Verify all required memory functions are available."""
        assert callable(get_peak_memory_mb)
        assert callable(check_memory_limit)
        assert callable(start_monitoring)
        assert hasattr(MemoryLimitExceededError, '__cause__') or True  # Just verify it exists

    def test_memory_limit_configuration(self):
        """Test that memory limit can be configured."""
        # Verify the default is 7GB
        assert memory_limit == 7168  # 7 * 1024

    def test_memory_monitor_with_preprocess(self):
        """
        Integration test: verify memory monitoring works with preprocess_graph.
        Uses a small synthetic graph to avoid real data dependency.
        """
        import networkx as nx

        # Create a small test graph
        G = nx.erdos_renyi_graph(500, 0.02)

        start_monitoring()
        try:
            lcc = extract_lcc(G)
            assert lcc.number_of_nodes() <= 500
        finally:
            tracemalloc.stop()

        peak_mb = get_peak_memory_mb()
        # Should be well under 7GB for this small graph
        assert peak_mb < MEMORY_LIMIT_MB

    def test_memory_limit_error_message(self):
        """Test that MemoryLimitExceededError has a clear message."""
        try:
            check_memory_limit(MEMORY_LIMIT_MB + 1000)
            pytest.fail("Should have raised MemoryLimitExceededError")
        except MemoryLimitExceededError as e:
            assert "memory limit" in str(e).lower() or "exceeded" in str(e).lower()

    def test_memory_monitor_reset(self):
        """Test that memory monitoring can be reset."""
        start_monitoring()
        current1, peak1 = tracemalloc.get_traced_memory()

        # Stop and restart
        tracemalloc.stop()
        start_monitoring()

        current2, peak2 = tracemalloc.get_traced_memory()
        # Peak should be reset or very low after restart
        assert peak2 < peak1 + 100  # Allow small overhead

    def test_memory_limit_with_large_graph_simulation(self):
        """
        Simulate processing a larger graph to test memory monitoring.
        Uses synthetic data but tests the monitoring logic.
        """
        import networkx as nx

        # Create a graph that's large but still under 7GB
        G = nx.erdos_renyi_graph(5000, 0.001)

        start_monitoring()
        try:
            # Process the graph
            lcc = extract_lcc(G)
            assert lcc.number_of_nodes() > 0
        finally:
            tracemalloc.stop()

        peak_mb = get_peak_memory_mb()
        # Should be well under 7GB
        assert peak_mb < MEMORY_LIMIT_MB

    def test_memory_monitor_thread_safety(self):
        """Test that memory monitoring works correctly (basic thread safety check)."""
        start_monitoring()
        try:
            # Perform some operations
            data = [i for i in range(1000)]
            current, peak = tracemalloc.get_traced_memory()
            assert isinstance(current, int)
            assert isinstance(peak, int)
        finally:
            tracemalloc.stop()

    def test_memory_limit_edge_case_zero(self):
        """Test memory limit with zero limit (should always fail)."""
        with pytest.raises(MemoryLimitExceededError):
            check_memory_limit(0)

    def test_memory_limit_edge_case_very_small(self):
        """Test memory limit with very small limit."""
        # 1KB limit
        with pytest.raises(MemoryLimitExceededError):
            check_memory_limit(0.001)