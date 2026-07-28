"""
Unit tests for memory constraint verification.

This module verifies that generating 50 networks of size N=500
fits within the 7GB RAM constraint (SC-001).
"""

import gc
import os
import sys
import unittest
from typing import List

import networkx as nx
import numpy as np

# Import the metrics utility to ensure consistent calculation
# The task requires verifying memory usage of network generation + metrics
try:
    # Adjust import based on project structure (src/ vs root)
    # Assuming standard layout: tests/unit -> code/utils
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from utils.metrics import calculate_structural_metrics
except ImportError:
    # Fallback if running in a different context, though tasks.md implies specific paths
    from utils.metrics import calculate_structural_metrics


# Constants from specification
N_NODES = 500
NUM_NETWORKS = 50
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3


def get_current_memory_usage() -> float:
    """
    Returns the current memory usage of the Python process in bytes.

    Uses `resource` on Unix/Linux/macOS or falls back to a safe estimate
    on Windows (where `resource` is unavailable).
    """
    if sys.platform != "win32":
        import resource
        # rusage.ru_maxrss is in kilobytes on Linux/macOS
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    else:
        # Windows fallback: psutil is often available, otherwise return 0
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            # If psutil is not available, we cannot measure accurately on Windows
            # We will skip the strict check but log a warning
            return 0.0


class TestMemoryConstraints(unittest.TestCase):
    """Tests to verify network generation stays within memory limits."""

    def test_50_networks_fit_in_7gb(self):
        """
        Verify that generating 50 networks of N=500 (ER, BA, WS)
        and calculating their structural metrics fits within 7GB RAM.

        This test simulates the worst-case scenario for User Story 1:
        - Generating multiple instances per topology
        - Storing them in memory simultaneously (or sequentially with metrics)
        - Calculating metrics which can be memory-intensive for large graphs
        """
        gc.collect()
        initial_memory = get_current_memory_usage()

        networks: List[nx.Graph] = []
        metrics_list = []

        try:
            # Generate 50 networks (mix of topologies to stress different structures)
            # 17 ER, 17 BA, 16 WS = 50
            seeds = list(range(50))

            for i, seed in enumerate(seeds):
                np.random.seed(seed)

                if i % 3 == 0:
                    # Erdős-Rényi
                    p = 0.01  # Low density to keep edge count reasonable
                    G = nx.erdos_renyi_graph(N_NODES, p, seed=seed)
                elif i % 3 == 1:
                    # Barabási-Albert
                    m = 3  # Number of edges to attach from a new node
                    G = nx.barabasi_albert_graph(N_NODES, m, seed=seed)
                else:
                    # Watts-Strogatz
                    k = 4  # Each node is connected to k nearest neighbors
                    p_rewire = 0.1
                    G = nx.watts_strogatz_graph(N_NODES, k, p_rewire, seed=seed)

                networks.append(G)

                # Calculate metrics immediately to ensure they are part of the memory footprint
                # This simulates the workflow in T013
                try:
                    metrics = calculate_structural_metrics(G)
                    metrics_list.append(metrics)
                except Exception:
                    # Some metrics (like assortativity) might fail on disconnected graphs
                    # We catch this to avoid test failure due to graph properties,
                    # but the memory is still allocated.
                    pass

                # Optional: Force garbage collection periodically if memory grows too fast
                if i % 10 == 0:
                    gc.collect()

        finally:
            # Cleanup to ensure we don't leave large objects in memory for other tests
            # However, the test passes only if we didn't exceed the limit DURING execution.
            # We check the peak usage (approximated by current usage after collection)
            # Note: ru_maxrss is the peak high-water mark on Linux, so we check that.
            pass

        gc.collect()
        final_memory = get_current_memory_usage()

        # On Linux, ru_maxrss is the peak usage since the process started.
        # On Windows (with psutil), we check current usage.
        # To be safe, we use the max of initial and final, but primarily rely on the OS peak tracker.
        peak_memory = final_memory if final_memory > initial_memory else initial_memory

        # If we couldn't measure (Windows without psutil), skip the assertion but print info
        if peak_memory == 0:
            self.skipTest("Memory measurement unavailable on this platform (Windows without psutil).")

        memory_gb = peak_memory / (1024**3)

        self.assertLess(
            peak_memory,
            MEMORY_LIMIT_BYTES,
            f"Memory limit exceeded: {memory_gb:.2f} GB used (limit: {MEMORY_LIMIT_GB} GB). "
            f"Generated {len(networks)} networks of size {N_NODES}."
        )

        # Additional sanity check: ensure we actually generated the networks
        self.assertEqual(len(networks), NUM_NETWORKS, "Failed to generate expected number of networks.")
        self.assertEqual(len(metrics_list), NUM_NETWORKS, "Failed to calculate metrics for all networks.")

    def test_single_large_network_metrics_memory(self):
        """
        Verify that calculating metrics on a single large network (N=500)
        does not cause an immediate memory spike that exceeds a safe threshold
        (e.g., 100MB for the calculation itself).
        """
        gc.collect()
        initial_memory = get_current_memory_usage()

        # Generate a dense BA network to stress the metric calculation
        G = nx.barabasi_albert_graph(N_NODES, m=10, seed=42)

        # Calculate all metrics
        metrics = calculate_structural_metrics(G)

        gc.collect()
        final_memory = get_current_memory_usage()

        if final_memory == 0:
            self.skipTest("Memory measurement unavailable.")

        delta_memory = final_memory - initial_memory
        # Allow some overhead, but ensure it's reasonable (e.g., < 500MB)
        self.assertLess(
            delta_memory,
            500 * 1024 * 1024,
            f"Metric calculation consumed excessive memory: {delta_memory / (1024*1024):.2f} MB"
        )

    def test_network_storage_efficiency(self):
        """
        Verify that storing 50 NetworkX graphs of N=500 nodes
        consumes less than 2GB of memory (allowing headroom for OS and Python overhead).
        """
        gc.collect()
        initial_memory = get_current_memory_usage()

        graphs = []
        for i in range(NUM_NETWORKS):
            seed = i
            # Use ER graphs as a baseline for memory usage
            G = nx.erdos_renyi_graph(N_NODES, 0.01, seed=seed)
            graphs.append(G)

        gc.collect()
        final_memory = get_current_memory_usage()

        if final_memory == 0:
            self.skipTest("Memory measurement unavailable.")

        memory_used_gb = (final_memory - initial_memory) / (1024**3)

        # 50 graphs of 500 nodes with ~2500 edges each should be well under 2GB
        # This is a sanity check to ensure no memory leaks in graph creation
        self.assertLess(
            memory_used_gb,
            2.0,
            f"Storing {NUM_NETWORKS} networks consumed {memory_used_gb:.2f} GB, expected < 2.0 GB"
        )

if __name__ == "__main__":
    unittest.main()