"""
Unit tests for the thermal solver module.
Specifically tests for disconnected graph handling and zero-resistance clamping.
"""
import pytest
import networkx as nx
import numpy as np
import logging
from io import StringIO

# Import the function under test based on the provided API surface
from thermal_solver import solve_kirchhoff_heat_flow, calculate_effective_conductivity, assign_thermal_resistance, build_edge_resistances


class TestDisconnectedGraphHandling:
    """Tests for T019: Verify disconnected graph returns zero conductivity and logs warning."""

    def test_disconnected_graph_returns_zero(self, caplog):
        """
        Verify that when a graph is disconnected, the solver returns 0.0 conductivity
        and logs the specific warning message:
        "Graph disconnected; conductivity set to 0.0"
        """
        # Arrange: Create a disconnected graph
        # Two separate triangles, no connection between them
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Component 1
        G.add_edges_from([(3, 4), (4, 5), (5, 3)])  # Component 2 (disconnected)

        # Mock parameters for the solver
        # We need to ensure the function is called with valid parameters
        # to trigger the connectivity check logic
        params = {
            'N': 6,
            'd': 50e-9,  # 50nm
            'l': 100e-9, # 100nm
            'material': 'Si',
            'seed': 42
        }

        # Capture log output
        caplog.set_level(logging.WARNING)

        # Act: Call the solver
        # Note: solve_kirchhoff_heat_flow returns the effective conductivity
        # and potentially other metrics, but we are interested in the conductivity value
        # and the side effect (logging).
        conductivity, _ = solve_kirchhoff_heat_flow(G, params)

        # Assert: Conductivity must be 0.0
        assert conductivity == 0.0, f"Expected conductivity 0.0 for disconnected graph, got {conductivity}"

        # Assert: Specific warning message must be logged
        expected_message = "Graph disconnected; conductivity set to 0.0"
        found_message = False
        for record in caplog.records:
            if record.levelno == logging.WARNING and expected_message in record.message:
                found_message = True
                break

        assert found_message, f"Expected warning log '{expected_message}' not found. Logs: {[r.message for r in caplog.records]}"

    def test_connected_graph_returns_positive(self):
        """
        Sanity check: Ensure a connected graph does NOT return zero conductivity.
        """
        # Arrange: Create a connected graph (a simple line)
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])

        params = {
            'N': 4,
            'd': 50e-9,
            'l': 100e-9,
            'material': 'Si',
            'seed': 42
        }

        # Act
        conductivity, _ = solve_kirchhoff_heat_flow(G, params)

        # Assert: Conductivity should be > 0
        assert conductivity > 0.0, f"Expected positive conductivity for connected graph, got {conductivity}"


class TestZeroResistanceClamping:
    """Tests for T020: Verify minimum thermal resistance threshold is enforced."""

    def test_zero_resistance_clamped(self):
        """
        Verify that when an edge has zero or near-zero resistance (e.g., due to
        extreme conductivity or geometry parameters), the solver clamps it to a
        minimum threshold to prevent division-by-zero or numerical instability.
        """
        # Arrange: Create a simple connected graph
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2)])

        # Parameters that might lead to very low resistance if not clamped
        # Using a very high conductivity material or very short length
        params = {
            'N': 3,
            'd': 10e-9,   # 10nm
            'l': 1e-9,    # 1nm (extremely short)
            'material': 'Ag', # Silver, high conductivity
            'seed': 42
        }

        # Act: Calculate edge resistances
        # This should trigger the clamping logic if resistance is too low
        edge_resistances = build_edge_resistances(G, params)

        # Assert: No resistance should be zero or negative
        for edge, r_val in edge_resistances.items():
            # The clamping threshold is typically defined in the solver
            # We check that the value is strictly positive
            assert r_val > 0.0, f"Edge {edge} has non-positive resistance: {r_val}"

        # Additional check: Verify that the solver can run without crashing
        conductivity, _ = solve_kirchhoff_heat_flow(G, params)
        assert conductivity >= 0.0, f"Conductivity should be non-negative, got {conductivity}"

    def test_extreme_parameters_clamped(self):
        """
        Test with parameters that would mathematically result in zero resistance
        (e.g., infinite conductivity or zero length) to ensure clamping works.
        """
        G = nx.Graph()
        G.add_edges_from([(0, 1)])

        # Simulate a scenario where resistance calculation might underflow
        # or be explicitly zero due to edge case parameters
        params = {
            'N': 2,
            'd': 1e-12,   # 1 picometer (unrealistic, tests edge case)
            'l': 0.0,     # Zero length
            'material': 'Si',
            'seed': 42
        }

        # Act: Calculate resistances
        edge_resistances = build_edge_resistances(G, params)

        # Assert: Resistance must be clamped to a minimum positive value
        for edge, r_val in edge_resistances.items():
            assert r_val > 0.0, f"Zero-length edge {edge} resulted in non-positive resistance: {r_val}"

        # Ensure the solver handles this gracefully
        conductivity, _ = solve_kirchhoff_heat_flow(G, params)
        assert isinstance(conductivity, (int, float)), "Conductivity must be a number"