"""
Integration tests for User Story 1: Network Topology Generation.

This module verifies that the generated networks meet the strict connectivity
and clustering coefficient target success rates defined in the specifications.

It relies on the generators implemented in `code/src/generators/` which are
expected to inherit from a base class and utilize shared retry logic.
"""
import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if not already present (for local execution)
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.utils.config import load_config
from code.src.utils.logging import log_run, clear_run_log

# Configuration constants for integration thresholds
# These align with FR-001 and SC-001 requirements for valid topology generation
MIN_SUCCESS_RATE = 0.85  # 85% of attempts must meet criteria
MIN_BATCH_SIZE = 10      # Minimum graphs to attempt for statistical relevance
CLUSTERING_TOLERANCE = 0.05  # Allowed deviation from target clustering


class TestIntegrationConnectivityAndClustering:
    """
    Integration tests verifying connectivity and clustering target success rates.
    
    These tests generate batches of networks using the configured parameters
    and verify that the success rate (graphs meeting all criteria) exceeds
    the MIN_SUCCESS_RATE threshold.
    """

    @pytest.fixture(autouse=True)
    def setup_integration_tests(self, config_fixture):
        """
        Setup fixture to ensure clean state for integration tests.
        Uses the config_fixture from conftest.py which loads the project config.
        """
        self.config = config_fixture
        self.batch_size = MIN_BATCH_SIZE
        # Clear any previous run logs to ensure isolated test execution
        clear_run_log()
        log_run("Integration Test Start", {"test": "connectivity_clustering"})

    def _validate_graph_metrics(self, G, topology_class, target_clustering=None):
        """
        Validate a single graph against connectivity and clustering criteria.
        
        Args:
            G (nx.Graph): The generated graph.
            topology_class (str): Name of the topology class for logging.
            target_clustering (float, optional): Expected clustering coefficient.
        
        Returns:
            bool: True if graph passes all checks, False otherwise.
        """
        # Check 1: Connectivity
        if not nx.is_connected(G):
            return False

        # Check 2: Clustering Coefficient (if target provided)
        if target_clustering is not None:
            actual_clustering = nx.average_clustering(G)
            if abs(actual_clustering - target_clustering) > CLUSTERING_TOLERANCE:
                return False

        return True

    def test_erdos_renyi_connectivity_rate(self):
        """
        Integration test for Erdős-Rényi graphs.
        
        Verifies that with the configured edge probability, the generator
        produces a connected graph at least MIN_SUCCESS_RATE of the time.
        """
        # Load parameters from config or use defaults for integration test
        # We assume config.yaml has 'generators': {'er': {'n': ..., 'p': ...}}
        try:
            params = self.config.get('generators', {}).get('er', {})
            n = params.get('n', 50)
            p = params.get('p', 0.1) # Ensure p is high enough for connectivity in test
        except Exception:
            n, p = 50, 0.15 # Fallback for robustness

        generator = ErdosRenyiGenerator(n=n, p=p, seed=42)
        
        successes = 0
        attempts = 0
        
        for i in range(self.batch_size):
            attempts += 1
            # The generator should handle retries internally, but we verify
            # the final output meets criteria.
            G = generator.generate()
            
            if G is None:
                # Generator failed to produce a valid graph after retries
                continue
                
            if self._validate_graph_metrics(G, "ErdosRenyi"):
                successes += 1

        success_rate = successes / attempts if attempts > 0 else 0.0
        
        # Assert success rate meets threshold
        assert success_rate >= MIN_SUCCESS_RATE, (
            f"ER Connectivity Failure: Success rate {success_rate:.2f} "
            f"below threshold {MIN_SUCCESS_RATE}. "
            f"Params: n={n}, p={p}, Attempts={attempts}"
        )

    def test_watts_strogatz_connectivity_and_clustering(self):
        """
        Integration test for Watts-Strogatz (Small-World) graphs.
        
        Verifies that the generator produces connected graphs with
        clustering coefficients close to the target value.
        """
        try:
            params = self.config.get('generators', {}).get('watts_strogatz', {})
            n = params.get('n', 50)
            k = params.get('k', 4)
            p_rewire = params.get('p', 0.1)
            target_clustering = params.get('target_clustering', 0.3)
        except Exception:
            n, k, p_rewire, target_clustering = 50, 4, 0.1, 0.3

        # For WS, we need to ensure the target clustering is achievable.
        # In integration tests, we often set a target that the algorithm
        # aims for via retry logic (as per T014 implementation).
        generator = WattsStrogatzGenerator(
            n=n, k=k, p=p_rewire, 
            target_clustering=target_clustering,
            seed=42
        )

        successes = 0
        attempts = 0

        for i in range(self.batch_size):
            attempts += 1
            G = generator.generate()

            if G is None:
                continue

            if self._validate_graph_metrics(G, "WattsStrogatz", target_clustering):
                successes += 1

        success_rate = successes / attempts if attempts > 0 else 0.0

        assert success_rate >= MIN_SUCCESS_RATE, (
            f"WS Connectivity/Clustering Failure: Success rate {success_rate:.2f} "
            f"below threshold {MIN_SUCCESS_RATE}. "
            f"Target Clustering: {target_clustering}"
        )

    def test_barabasi_albert_connectivity_rate(self):
        """
        Integration test for Barabási-Albert (Scale-Free) graphs.
        
        Verifies that the preferential attachment process consistently
        yields connected graphs.
        """
        try:
            params = self.config.get('generators', {}).get('barabasi_albert', {})
            n = params.get('n', 50)
            m = params.get('m', 2) # Number of edges to attach from new node
        except Exception:
            n, m = 50, 2

        generator = BarabasiAlbertGenerator(n=n, m=m, seed=42)

        successes = 0
        attempts = 0

        for i in range(self.batch_size):
            attempts += 1
            G = generator.generate()

            if G is None:
                continue

            # BA graphs with m>=1 are theoretically connected, but we verify
            if self._validate_graph_metrics(G, "BarabasiAlbert"):
                successes += 1

        success_rate = successes / attempts if attempts > 0 else 0.0

        assert success_rate >= MIN_SUCCESS_RATE, (
            f"BA Connectivity Failure: Success rate {success_rate:.2f} "
            f"below threshold {MIN_SUCCESS_RATE}. "
            f"Params: n={n}, m={m}"
        )

    def test_batch_consistency_metrics(self):
        """
        Regression test to ensure metrics are stable across a batch.
        
        Verifies that the distribution of metrics (clustering, path length)
        does not have extreme outliers that would indicate generator failure.
        """
        params = self.config.get('generators', {}).get('er', {})
        n = params.get('n', 50)
        p = params.get('p', 0.15)

        generator = ErdosRenyiGenerator(n=n, p=p, seed=42)
        
        clustering_values = []
        
        for i in range(self.batch_size):
            G = generator.generate()
            if G and nx.is_connected(G):
                clustering_values.append(nx.average_clustering(G))
        
        if not clustering_values:
            pytest.fail("No valid connected graphs generated for batch consistency test.")
        
        # Check for statistical sanity: mean should not be NaN or Inf
        mean_clustering = np.mean(clustering_values)
        std_clustering = np.std(clustering_values)
        
        assert not np.isnan(mean_clustering), "Mean clustering is NaN"
        assert not np.isinf(mean_clustering), "Mean clustering is Inf"
        assert std_clustering < 0.5, "Clustering variance is unexpectedly high"