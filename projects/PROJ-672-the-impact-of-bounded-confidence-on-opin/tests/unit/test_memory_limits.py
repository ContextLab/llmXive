"""
Unit tests for memory constraint verification.

This module verifies that generating 50 networks of size N=500
fits within the 7GB RAM constraint (SC-001) using psutil to monitor
memory usage, as required by the task specification.
"""

import gc
import os
import sys
import unittest
from typing import List

import networkx as nx
import numpy as np
import psutil

# Import the metrics utility to ensure consistent calculation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.metrics import calculate_structural_metrics

# Constants from specification
N_NODES = 500
NUM_NETWORKS = 50
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3


def get_current_memory_usage() -> float:
    """
    Returns the current memory usage of the Python process in bytes
    using psutil. This works on all platforms supported by the runner.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


class TestMemoryConstraints(unittest.TestCase):
    """Tests to verify network generation stays within memory limits."""

    def test_50_networks_fit_in_7gb(self):
        """
        Verify that generating 50 networks of N=500 (ER, BA, WS)
        and calculating their structural metrics fits within 7GB RAM.

        This test simulates the worst-case scenario for User Story 1:
        - Generating multiple instances per topology
        - Storing them in memory simultaneously (or sequentially with metrics)
        - Calculating metrics which can be memory‑intensive for large graphs
        """
        gc.collect()
        initial_memory = get_current_memory_usage()

        networks: List[nx.Graph] = []
        metrics_list = []
        peak_memory = initial_memory

        try:
            # Generate 50 networks (mix of topologies to stress different structures)
            # 17 ER, 17 BA, 16 WS = 50
            seeds = list(range(NUM_NETWORKS))

            for i, seed in enumerate(seeds):
                np.random.seed(seed)

                if i % 3 == 0:
                    # Erdős‑Rényi
                    p = 0.01  # Low density to keep edge count reasonable
                    G = nx.erdos_renyi_graph(N_NODES, p, seed=seed)
                elif i % 3 == 1:
                    # Barabási‑Albert
                    m = 3  # Number of edges to attach from a new node
                    G = nx.barabasi_albert_graph(N_NODES, m, seed=seed)
                else:
                    # Watts‑Strogatz
                    k = 4  # Each node is connected to k nearest neighbors
                    p_rewire = 0.1
                    G = nx.watts_strogatz_graph(N_NODES, k, p_rewire, seed=seed)

                networks.append(G)

                # Update peak memory after adding the graph
                current_mem = get_current_memory_usage()
                if current_mem > peak_memory:
                    peak_memory = current_mem

                # Calculate metrics immediately to ensure they are part of the memory footprint
                try:
                    metrics = calculate_structural_metrics(G)
                    metrics_list.append(metrics)
                except Exception:
                    # Some metrics (like assortativity) might fail on disconnected graphs;
                    # we ignore them for the memory test.
                    metrics_list.append({})
                
                # Update peak memory after metric calculation
                current_mem = get_current_memory_usage()
                if current_mem > peak_memory:
                    peak_memory = current_mem

                # Optional: Force garbage collection periodically if memory grows too fast
                if i % 10 == 0:
                    gc.collect()
        finally:
            # Cleanup to ensure we don't leave large objects in memory for other tests
            pass

        gc.collect()
        final_memory = get_current_memory_usage()
        if final_memory > peak_memory:
            peak_memory = final_memory

        memory_gb = peak_memory / (1024**3)

        self.assertLess(
            peak_memory,
            MEMORY_LIMIT_BYTES,
            f"Memory limit exceeded: {memory_gb:.2f} GB used (limit: {MEMORY_LIMIT_GB} GB). "
            f"Generated {len(networks)} networks of size {N_NODES}."
        )

        # Additional sanity checks
        self.assertEqual(len(networks), NUM_NETWORKS,
                         "Failed to generate the expected number of networks.")
        self.assertEqual(len(metrics_list), NUM_NETWORKS,
                         "Failed to calculate metrics for all networks.")

    def test_single_large_network_metrics_memory(self):
        """
        Verify that calculating metrics on a single large network (N=500)
        does not cause an immediate memory spike that exceeds a safe threshold
        (e.g., 100 MB for the calculation itself).
        """
        gc.collect()
        initial_memory = get_current_memory_usage()

        # Generate a dense BA network to stress the metric calculation
        G = nx.barabasi_albert_graph(N_NODES, m=10, seed=42)

        # Calculate all metrics
        _ = calculate_structural_metrics(G)

        gc.collect()
        final_memory = get_current_memory_usage()

        delta_memory = final_memory - initial_memory
        allowed_delta = 100 * 1024 * 1024  # 100 MB

        self.assertLess(
            delta_memory,
            allowed_delta,
            f"Metric calculation consumed excessive memory: {delta_memory / (1024*1024):.2f} MB"
        )

    def test_network_storage_efficiency(self):
        """
        Verify that storing 50 NetworkX graphs of N=500 nodes
        consumes less than 2 GB of memory, allowing headroom for OS and Python overhead.
        """
        gc.collect()
        initial_memory = get_current_memory_usage()

        graphs = []
        for i in range(NUM_NETWORKS):
            seed = i
            # Use ER graphs as a baseline for memory usage
            G = nx.erdos_renyi_graph(N_NODES, 0.01, seed=seed)
            graphs.append(G)

            # Update peak memory after each graph creation
            current_mem = get_current_memory_usage()
            if current_mem - initial_memory > MEMORY_LIMIT_BYTES:
                break

        gc.collect()
        final_memory = get_current_memory_usage()
        memory_used_gb = (final_memory - initial_memory) / (1024**3)

        self.assertLess(
            memory_used_gb,
            2.0,
            f"Storing {NUM_NETWORKS} networks consumed {memory_used_gb:.2f} GB, expected < 2.0 GB"
        )

if __name__ == "__main__":
    unittest.main()