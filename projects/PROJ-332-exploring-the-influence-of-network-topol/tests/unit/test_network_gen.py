"""
Unit tests for graph generation accuracy in generate_networks.py.
Specifically verifies that the generated network's average degree
is within the specified tolerance (±5%) of the target degree.
"""
import pytest
import networkx as nx
import sys
import os

# Add the code directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from generate_networks import generate_nanowire_network


class TestAvgDegreeWithinTolerance:
    """
    Test suite for verifying average degree accuracy in generated networks.
    """

    @pytest.mark.parametrize(
        "target_degree, node_count, tolerance",
        [
            (2.0, 50, 0.05),   # Low degree, small network
            (4.0, 100, 0.05),  # Medium degree, medium network
            (6.0, 200, 0.05),  # High degree, larger network
            (3.5, 150, 0.05),  # Non-integer degree
        ]
    )
    def test_avg_degree_within_tolerance(self, target_degree, node_count, tolerance):
        """
        Verify that the generated graph's average degree is within ±5% of the target.

        Args:
            target_degree: The desired average node degree.
            node_count: Number of nodes in the graph.
            tolerance: Acceptable deviation (default 5% = 0.05).
        """
        # Generate the network
        # We use a fixed seed for reproducibility in testing
        graph = generate_nanowire_network(
            N=node_count,
            target_avg_degree=target_degree,
            seed=42
        )

        # Calculate the actual average degree
        # Average degree = 2 * |E| / |V|
        actual_avg_degree = 2 * graph.number_of_edges() / graph.number_of_nodes()

        # Calculate the allowed deviation
        allowed_deviation = target_degree * tolerance

        # Assert the actual degree is within the tolerance range
        lower_bound = target_degree - allowed_deviation
        upper_bound = target_degree + allowed_deviation

        assert lower_bound <= actual_avg_degree <= upper_bound, (
            f"Average degree {actual_avg_degree:.4f} is outside the tolerance range "
            f"[{lower_bound:.4f}, {upper_bound:.4f}] for target {target_degree} "
            f"(tolerance: ±{tolerance*100}%)"
        )

    def test_avg_degree_exact_match_large_sample(self):
        """
        Test with a larger sample size where the generation algorithm
        should converge very close to the target degree.
        """
        target_degree = 4.0
        node_count = 500
        tolerance = 0.02  # Tighter tolerance for larger graph

        graph = generate_nanowire_network(
            N=node_count,
            target_avg_degree=target_degree,
            seed=123
        )

        actual_avg_degree = 2 * graph.number_of_edges() / graph.number_of_nodes()
        allowed_deviation = target_degree * tolerance

        assert abs(actual_avg_degree - target_degree) <= allowed_deviation, (
            f"Large sample test failed: {actual_avg_degree} vs target {target_degree}"
        )

    def test_consistency_across_seeds(self):
        """
        Verify that multiple runs with different seeds produce
        average degrees within tolerance of the target.
        """
        target_degree = 5.0
        node_count = 100
        tolerance = 0.05
        seeds = [1, 42, 123, 999, 2024]

        results = []
        for seed in seeds:
            graph = generate_nanowire_network(
                N=node_count,
                target_avg_degree=target_degree,
                seed=seed
            )
            avg_deg = 2 * graph.number_of_edges() / graph.number_of_nodes()
            results.append(avg_deg)

            assert abs(avg_deg - target_degree) <= (target_degree * tolerance), (
                f"Seed {seed} produced avg degree {avg_deg} outside tolerance"
            )

        # Log the range of results for debugging
        assert max(results) - min(results) < (target_degree * 0.1), (
            f"Results too variable across seeds: min={min(results)}, max={max(results)}"
        )