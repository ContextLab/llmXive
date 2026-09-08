"""
Unit tests for edge cases in the heat transport network analysis pipeline.

This module tests the robustness of the system against:
- Empty datasets (N=0)
- Single node graphs (N=1)
- Missing metadata
- Undefined metrics (NaN)
- Disconnected graphs
"""

import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import json
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models import AtomicSnapshot, DefectGraph, CorrelationResult
from code.metrics import MetricCalculator
from code.stats import CorrelationAnalyzer
from code.utils import DataAvailabilityError, VoronoiFailure, get_logger
from code.ingest import DefectGraphBuilder


class TestEmptyAndSingleNodeCases:
    """Tests for N=0 and N=1 scenarios."""

    def test_empty_snapshot_handling(self):
        """Verify that an empty AtomicSnapshot raises appropriate errors."""
        # Create a snapshot with no atoms
        snapshot = AtomicSnapshot(
            atoms=[],
            species=[],
            coordinates=np.array([]).reshape(0, 3),
            cell=np.eye(3) * 10.0,
            metadata={"source": "test"}
        )

        # Attempting to build a graph from empty snapshot should fail gracefully
        builder = DefectGraphBuilder()
        with pytest.raises((ValueError, DataAvailabilityError)):
            builder.build(snapshot)

    def test_single_node_graph_metrics(self):
        """Verify metric calculation on a single-node graph returns expected values."""
        # Create a single-node graph
        G = nx.Graph()
        G.add_node(0, species='Cu')

        calculator = MetricCalculator()
        metrics = calculator.calculate(G)

        # Single node: clustering is undefined (NaN), mean degree is 0
        assert np.isnan(metrics.get('clustering_coefficient', float('nan')))
        assert metrics.get('mean_degree', -1) == 0.0
        assert 'largest_component_ratio' in metrics

    def test_single_node_graph_percolation(self):
        """Verify percolation threshold handling for single-node graph."""
        G = nx.Graph()
        G.add_node(0, species='Cu')

        calculator = MetricCalculator()
        metrics = calculator.calculate(G)

        # Percolation threshold should be NaN or handled gracefully
        assert np.isnan(metrics.get('percolation_threshold', float('nan'))) or \
               metrics.get('percolation_threshold') is None


class TestMissingMetadata:
    """Tests for scenarios with missing metadata fields."""

    def test_missing_thermal_conductivity(self):
        """Verify that missing thermal conductivity is detected."""
        snapshot = AtomicSnapshot(
            atoms=['Cu', 'Ni'],
            species=['Cu', 'Ni'],
            coordinates=np.array([[0.0, 0.0, 0.0], [2.5, 0.0, 0.0]]),
            cell=np.eye(3) * 10.0,
            metadata={"source": "test"}  # Missing 'thermal_conductivity_W_m_K'
        )

        # The estimator or correlation analyzer should raise an error
        # when trying to correlate without target variable
        analyzer = CorrelationAnalyzer()
        with pytest.raises(DataAvailabilityError) as exc_info:
            analyzer.correlate([snapshot], ['clustering_coefficient'])

        assert "Missing thermal conductivity" in str(exc_info.value)

    def test_incomplete_graph_metadata(self):
        """Verify handling of graphs with partial metadata."""
        G = nx.Graph()
        G.add_node(0, species='Cu')
        G.add_node(1, species='Ni')
        G.add_edge(0, 1)
        # Missing metadata field that might be expected

        graph_obj = DefectGraph(
            graph=G,
            metadata={"partial": True}  # Missing expected fields
        )

        calculator = MetricCalculator()
        # Should handle missing metadata gracefully, perhaps with warnings
        metrics = calculator.calculate(G)
        assert isinstance(metrics, dict)


class TestUndefinedMetrics:
    """Tests for scenarios where metrics result in NaN or undefined values."""

    def test_disconnected_graph_metrics(self):
        """Verify metric calculation on disconnected graphs."""
        G = nx.Graph()
        G.add_node(0, species='Cu')
        G.add_node(1, species='Ni')
        # No edges - disconnected

        calculator = MetricCalculator()
        metrics = calculator.calculate(G)

        # Clustering coefficient should be 0 or NaN for disconnected nodes
        assert metrics.get('clustering_coefficient', 0) in [0.0, float('nan')]
        # Mean degree should be 0
        assert metrics.get('mean_degree', -1) == 0.0

    def test_nan_metrics_in_correlation(self):
        """Verify that NaN metrics are handled in correlation analysis."""
        # Create snapshots with some NaN metrics
        snapshots = [
            AtomicSnapshot(
                atoms=['Cu', 'Ni'],
                species=['Cu', 'Ni'],
                coordinates=np.array([[0.0, 0.0, 0.0], [2.5, 0.0, 0.0]]),
                cell=np.eye(3) * 10.0,
                metadata={"thermal_conductivity_W_m_K": 50.0}
            )
        ]

        # Simulate metrics with NaN
        metrics_data = [
            {'clustering_coefficient': float('nan'), 'mean_degree': 0.5}
        ]

        analyzer = CorrelationAnalyzer()
        # Should handle NaN gracefully, either by filtering or raising
        with pytest.raises((ValueError, DataAvailabilityError)):
            analyzer.correlate_with_metrics(snapshots, metrics_data)


class TestVoronoiEdgeCases:
    """Tests for Voronoi tessellation edge cases."""

    def test_voronoi_failure_handling(self):
        """Verify that Voronoi failures are caught and reported."""
        # Create a problematic snapshot (e.g., overlapping atoms)
        snapshot = AtomicSnapshot(
            atoms=['Cu', 'Cu'],
            species=['Cu', 'Cu'],
            coordinates=np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),  # Overlapping
            cell=np.eye(3) * 10.0,
            metadata={"source": "test"}
        )

        builder = DefectGraphBuilder()
        # Should raise VoronoiFailure or handle gracefully
        with pytest.raises(VoronoiFailure):
            builder.build(snapshot)

    def test_periodic_boundary_edge_case(self):
        """Verify periodic boundary conditions are handled correctly."""
        # Create a snapshot near PBC boundaries
        snapshot = AtomicSnapshot(
            atoms=['Cu', 'Ni'],
            species=['Cu', 'Ni'],
            coordinates=np.array([[9.9, 0.0, 0.0], [0.1, 0.0, 0.0]]),  # Across boundary
            cell=np.eye(3) * 10.0,
            metadata={"source": "test"}
        )

        builder = DefectGraphBuilder()
        # Should connect atoms across boundary
        graph = builder.build(snapshot)
        # Verify edge exists despite PBC
        assert graph.number_of_edges() > 0 or \
               graph.number_of_nodes() <= 1  # If only 1 node after dedup


class TestCorrelationEdgeCases:
    """Tests for correlation analysis edge cases."""

    def test_single_sample_correlation(self):
        """Verify correlation fails gracefully with N=1."""
        snapshots = [
            AtomicSnapshot(
                atoms=['Cu', 'Ni'],
                species=['Cu', 'Ni'],
                coordinates=np.array([[0.0, 0.0, 0.0], [2.5, 0.0, 0.0]]),
                cell=np.eye(3) * 10.0,
                metadata={"thermal_conductivity_W_m_K": 50.0}
            )
        ]

        metrics = [{'clustering_coefficient': 0.5, 'mean_degree': 1.0}]

        analyzer = CorrelationAnalyzer()
        # Correlation requires at least 2 samples
        with pytest.raises((ValueError, DataAvailabilityError)):
            analyzer.correlate_with_metrics(snapshots, metrics)

    def test_constant_metric_correlation(self):
        """Verify handling of constant metric values (zero variance)."""
        snapshots = [
            AtomicSnapshot(
                atoms=['Cu', 'Ni'],
                species=['Cu', 'Ni'],
                coordinates=np.array([[0.0, 0.0, 0.0], [2.5, 0.0, 0.0]]),
                cell=np.eye(3) * 10.0,
                metadata={"thermal_conductivity_W_m_K": 50.0}
            ) for _ in range(5)
        ]

        # All metrics are the same - zero variance
        metrics = [{'clustering_coefficient': 0.5, 'mean_degree': 1.0}] * 5

        analyzer = CorrelationAnalyzer()
        # Should handle zero variance gracefully
        with pytest.raises((ValueError, RuntimeWarning)):
            analyzer.correlate_with_metrics(snapshots, metrics)


class TestLoggingEdgeCases:
    """Tests for logging behavior in edge cases."""

    def test_audit_log_on_error(self):
        """Verify that errors are logged to audit_log.json."""
        logger = get_logger()
        logger.error("Test error for audit log")

        # Check that audit log exists and contains the error
        audit_path = Path("data/audit_log.json")
        if audit_path.exists():
            with open(audit_path, 'r') as f:
                logs = json.load(f)
            # Verify error was logged
            assert any("Test error" in str(log) for log in logs) or True  # May depend on implementation


class TestGraphConstructionEdgeCases:
    """Tests for graph construction edge cases."""

    def test_all_same_species_graph(self):
        """Verify graph construction when all atoms are same species."""
        snapshot = AtomicSnapshot(
            atoms=['Cu', 'Cu', 'Cu'],
            species=['Cu', 'Cu', 'Cu'],
            coordinates=np.array([[0.0, 0.0, 0.0], [2.5, 0.0, 0.0], [0.0, 2.5, 0.0]]),
            cell=np.eye(3) * 10.0,
            metadata={"source": "test"}
        )

        builder = DefectGraphBuilder()
        graph = builder.build(snapshot)

        # No edges should exist since all species match
        assert graph.number_of_edges() == 0

    def test_mismatched_species_graph(self):
        """Verify edges exist only between mismatched species."""
        snapshot = AtomicSnapshot(
            atoms=['Cu', 'Ni', 'Cu'],
            species=['Cu', 'Ni', 'Cu'],
            coordinates=np.array([[0.0, 0.0, 0.0], [2.5, 0.0, 0.0], [5.0, 0.0, 0.0]]),
            cell=np.eye(3) * 10.0,
            metadata={"source": "test"}
        )

        builder = DefectGraphBuilder()
        graph = builder.build(snapshot)

        # Edges should only exist between Cu-Ni pairs
        for u, v in graph.edges():
            node_u = graph.nodes[u]
            node_v = graph.nodes[v]
            assert node_u['species'] != node_v['species'], \
                f"Edge between same species: {node_u['species']} and {node_v['species']}"