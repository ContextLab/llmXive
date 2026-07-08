"""
Integration tests for User Story 1: Network Topology Generation.

These tests verify that the generators produce connected graphs with
clustering coefficients meeting target thresholds within a specified
success rate.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple

import networkx as nx
import numpy as np

from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.metrics import extract_all_metrics, compute_clustering_coefficients
from code.src.generators.base import BaseGenerator

# Constants for integration tests
MIN_SUCCESS_RATE = 0.80  # At least 80% of graphs must meet criteria
MAX_GENERATION_ATTEMPTS = 50  # Max attempts per graph to meet criteria

class TestIntegrationConnectivityAndClustering:
    """
    Integration tests verifying connectivity and clustering target success rates.
    """
    
    def _generate_graph_with_retry(
        self, 
        generator: BaseGenerator, 
        config: Dict[str, Any],
        target_clustering: float,
        tolerance: float = 0.05
    ) -> Tuple[bool, nx.Graph]:
        """
        Attempt to generate a graph that meets connectivity and clustering targets.
        
        Args:
            generator: The generator instance to use.
            config: Configuration for the generator.
            target_clustering: Target clustering coefficient.
            tolerance: Acceptable deviation from target.
        
        Returns:
            Tuple of (success: bool, graph: nx.Graph or None)
        """
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            try:
                # Generate graph
                graph = generator.generate(**config)
                
                if graph is None:
                    continue
                
                # Check connectivity
                if not nx.is_connected(graph):
                    continue
                
                # Check clustering coefficient
                metrics = extract_all_metrics(graph)
                actual_clustering = metrics.get('average_clustering', 0.0)
                
                if abs(actual_clustering - target_clustering) <= tolerance:
                    return True, graph
            
            except Exception as e:
                # Log attempt failure but continue trying
                continue
        
        return False, None
    
    def _run_success_rate_test(
        self, 
        generator: BaseGenerator, 
        config: Dict[str, Any],
        target_clustering: float,
        num_trials: int = 20,
        tolerance: float = 0.05
    ) -> float:
        """
        Run a batch of generation attempts and return the success rate.
        
        Args:
            generator: The generator instance.
            config: Configuration for generation.
            target_clustering: Target clustering coefficient.
            num_trials: Number of graphs to attempt to generate.
            tolerance: Acceptable deviation from target.
        
        Returns:
            Success rate (float between 0.0 and 1.0)
        """
        successes = 0
        
        for i in range(num_trials):
            # Update seed for each trial to ensure diversity
            config['seed'] = 42 + i
            success, _ = self._generate_graph_with_retry(
                generator, config, target_clustering, tolerance
            )
            if success:
                successes += 1
        
        return successes / num_trials
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_er_connectivity_success_rate(self, temp_output_dir):
        """
        Test that Erdős-Rényi generator achieves target connectivity rate.
        
        ER graphs are connected with high probability when p > ln(n)/n.
        We test with parameters that should yield high connectivity.
        """
        config = {
            'n': 50,
            'p': 0.15,  # High enough for connectivity
            'seed': 42
        }
        target_clustering = 0.1  # ER typically has low clustering
        
        generator = ErdosRenyiGenerator()
        success_rate = self._run_success_rate_test(
            generator, config, target_clustering, num_trials=20
        )
        
        # Log results
        results = {
            'generator': 'ErdosRenyi',
            'config': config,
            'target_clustering': target_clustering,
            'success_rate': success_rate,
            'num_trials': 20
        }
        
        output_path = temp_output_dir / 'er_integration_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert success rate meets threshold
        assert success_rate >= MIN_SUCCESS_RATE, (
            f"ER generator success rate {success_rate:.2f} "
            f"below minimum {MIN_SUCCESS_RATE}"
        )
    
    def test_sw_connectivity_and_clustering_success_rate(self, temp_output_dir):
        """
        Test that Watts-Strogatz generator achieves connectivity and clustering targets.
        
        WS graphs are constructed to be connected and have tunable clustering.
        This is the primary test for clustering target verification.
        """
        config = {
            'n': 60,
            'k': 6,  # Each node connected to 3 neighbors on each side
            'p': 0.1,  # Low rewiring probability preserves clustering
            'seed': 42
        }
        target_clustering = 0.5  # WS should have high clustering
        
        generator = WattsStrogatzGenerator()
        success_rate = self._run_success_rate_test(
            generator, config, target_clustering, num_trials=20
        )
        
        # Log results
        results = {
            'generator': 'WattsStrogatz',
            'config': config,
            'target_clustering': target_clustering,
            'success_rate': success_rate,
            'num_trials': 20
        }
        
        output_path = temp_output_dir / 'sw_integration_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert success rate meets threshold
        assert success_rate >= MIN_SUCCESS_RATE, (
            f"WS generator success rate {success_rate:.2f} "
            f"below minimum {MIN_SUCCESS_RATE}"
        )
    
    def test_sf_connectivity_success_rate(self, temp_output_dir):
        """
        Test that Barabási-Albert generator achieves connectivity.
        
        BA graphs are preferential attachment networks that are typically
        connected, but clustering is naturally lower and harder to control.
        We test connectivity primarily here.
        """
        config = {
            'n': 50,
            'm': 3,  # Attach to 3 existing nodes
            'seed': 42
        }
        # BA graphs have lower clustering, so we use a wider tolerance
        target_clustering = 0.1
        tolerance = 0.15  # Wider tolerance for BA

        generator = BarabasiAlbertGenerator()
        success_rate = self._run_success_rate_test(
            generator, config, target_clustering, num_trials=20, tolerance=tolerance
        )
        
        # Log results
        results = {
            'generator': 'BarabasiAlbert',
            'config': config,
            'target_clustering': target_clustering,
            'success_rate': success_rate,
            'num_trials': 20,
            'tolerance': tolerance
        }
        
        output_path = temp_output_dir / 'sf_integration_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert success rate meets threshold
        assert success_rate >= MIN_SUCCESS_RATE, (
            f"BA generator success rate {success_rate:.2f} "
            f"below minimum {MIN_SUCCESS_RATE}"
        )
    
    def test_batch_generation_and_metrics_extraction(self, temp_output_dir):
        """
        Integration test: Generate a batch of graphs, extract metrics,
        and verify the distribution of metrics matches expectations.
        """
        # Generate a batch of WS graphs
        batch_size = 30
        graphs = []
        metrics_list = []
        
        config = {
            'n': 50,
            'k': 4,
            'p': 0.1,
            'seed': 100
        }
        
        generator = WattsStrogatzGenerator()
        
        for i in range(batch_size):
            config['seed'] = 100 + i
            try:
                graph = generator.generate(**config)
                if graph and nx.is_connected(graph):
                    graphs.append(graph)
                    metrics = extract_all_metrics(graph)
                    metrics_list.append(metrics)
            except Exception:
                continue
        
        # Verify we got enough graphs
        assert len(graphs) >= int(batch_size * 0.7), (
            f"Only generated {len(graphs)} connected graphs out of {batch_size}"
        )
        
        # Compute statistics on clustering coefficients
        clustering_values = [m['average_clustering'] for m in metrics_list]
        mean_clustering = np.mean(clustering_values)
        std_clustering = np.std(clustering_values)
        
        # Verify clustering is in expected range for WS (0.4 to 0.8 typically)
        assert 0.3 <= mean_clustering <= 0.9, (
            f"Mean clustering {mean_clustering:.3f} out of expected range for WS"
        )
        
        # Save batch metrics
        batch_results = {
            'generator': 'WattsStrogatz',
            'batch_size': batch_size,
            'successful_generations': len(graphs),
            'clustering_stats': {
                'mean': float(mean_clustering),
                'std': float(std_clustering),
                'min': float(min(clustering_values)),
                'max': float(max(clustering_values))
            },
            'metrics_sample': metrics_list[:5]  # Save first 5 for inspection
        }
        
        output_path = temp_output_dir / 'batch_metrics.json'
        with open(output_path, 'w') as f:
            json.dump(batch_results, f, indent=2)
        
        # Assert clustering consistency
        assert std_clustering < 0.2, (
            f"Clustering std {std_clustering:.3f} too high, indicates instability"
        )
    
    def test_overall_success_rate_aggregation(self, temp_output_dir):
        """
        Aggregate success rates across all generators and verify overall performance.
        """
        generators_configs = [
            (ErdosRenyiGenerator(), {'n': 40, 'p': 0.15}, 0.08, 0.05),
            (WattsStrogatzGenerator(), {'n': 50, 'k': 4, 'p': 0.1}, 0.5, 0.05),
            (BarabasiAlbertGenerator(), {'n': 40, 'm': 2}, 0.1, 0.15)
        ]
        
        overall_results = []
        
        for generator, config, target_clust, tol in generators_configs:
            success_rate = self._run_success_rate_test(
                generator, config, target_clust, num_trials=15, tolerance=tol
            )
            overall_results.append({
                'generator': type(generator).__name__,
                'success_rate': success_rate,
                'target': target_clust
            })
        
        # Calculate overall success rate
        avg_success_rate = np.mean([r['success_rate'] for r in overall_results])
        
        # Log aggregated results
        aggregated_results = {
            'overall_average_success_rate': float(avg_success_rate),
            'minimum_required': MIN_SUCCESS_RATE,
            'individual_results': overall_results
        }
        
        output_path = temp_output_dir / 'aggregated_integration_results.json'
        with open(output_path, 'w') as f:
            json.dump(aggregated_results, f, indent=2)
        
        # Assert overall performance
        assert avg_success_rate >= MIN_SUCCESS_RATE, (
            f"Overall average success rate {avg_success_rate:.2f} "
            f"below minimum {MIN_SUCCESS_RATE}"
        )