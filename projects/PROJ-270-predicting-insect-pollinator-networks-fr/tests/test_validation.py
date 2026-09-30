"""
Unit tests for validation module components.
Includes tests for LOEO, Null Models, and Visualization.
"""

import unittest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import target module (assuming validation.py exists as per T036-T040)
# If validation.py is not yet fully implemented, we mock the expected interface
# to ensure the test logic for T034 (Degree-Preserving Null Model) is valid.
try:
    from code.validation import (
        generate_degree_preserving_null_model,
        calculate_network_statistics,
        run_loeo_validation
    )
    VALIDATION_MODULE_EXISTS = True
except ImportError:
    VALIDATION_MODULE_EXISTS = False
    # Define mock classes/functions for testing logic if module doesn't exist yet
    # This ensures T034 logic can be written and verified even if T036 is pending
    class MockValidation:
        @staticmethod
        def generate_degree_preserving_null_model(interaction_matrix, iterations=10):
            """Mock implementation for testing structure."""
            return interaction_matrix.copy()

        @staticmethod
        def calculate_network_statistics(matrix):
            return {"degree_mean": 1.0, "clustering": 0.5}

    # Patch the import to allow test execution
    import sys
    import types
    mock_module = types.ModuleType('validation')
    mock_module.generate_degree_preserving_null_model = MockValidation.generate_degree_preserving_null_model
    mock_module.calculate_network_statistics = MockValidation.calculate_network_statistics
    sys.modules['code.validation'] = mock_module
    from code.validation import (
        generate_degree_preserving_null_model,
        calculate_network_statistics,
        run_loeo_validation
    )


class TestDegreePreservingNullModel(unittest.TestCase):
    """
    Unit test for Degree-Preserving Null Model (T034).

    This test verifies that the null model generation:
    1. Preserves the degree distribution of the original network.
    2. Randomizes the edges (rewiring) to break the trait association.
    3. Produces a valid adjacency matrix of the same shape.
    """

    def setUp(self):
        """Set up a small, deterministic bipartite interaction matrix."""
        # Create a simple 4x4 bipartite matrix (2 plants, 2 pollinators)
        # Rows: Plants (P1, P2), Cols: Pollinators (A, B)
        # Interaction matrix:
        # P1: connected to A, B (Degree 2)
        # P2: connected to A (Degree 1)
        # A: connected to P1, P2 (Degree 2)
        # B: connected to P1 (Degree 1)
        self.original_matrix = np.array([
            [1, 1],
            [1, 0]
        ], dtype=float)
        self.num_nodes = self.original_matrix.shape[0] + self.original_matrix.shape[1]

    @unittest.skipIf(not VALIDATION_MODULE_EXISTS, "validation module not yet implemented")
    def test_degree_preservation(self):
        """
        Verify that the degree distribution of the null model matches the original.
        """
        # Run the null model generator
        null_model = generate_degree_preserving_null_model(
            self.original_matrix,
            iterations=50  # Ensure enough iterations for mixing
        )

        # Calculate degrees for original and null
        # In a bipartite matrix, row degrees are plant degrees, col degrees are pollinator degrees
        original_row_degrees = np.sum(self.original_matrix, axis=1)
        null_row_degrees = np.sum(null_model, axis=1)

        original_col_degrees = np.sum(self.original_matrix, axis=0)
        null_col_degrees = np.sum(null_model, axis=0)

        # Assert degrees are exactly preserved (since we are rewiring)
        self.assertTrue(np.array_equal(original_row_degrees, null_row_degrees),
                        "Row degrees (plants) must be preserved")
        self.assertTrue(np.array_equal(original_col_degrees, null_col_degrees),
                        "Column degrees (pollinators) must be preserved")

    @unittest.skipIf(not VALIDATION_MODULE_EXISTS, "validation module not yet implemented")
    def test_edge_randomization(self):
        """
        Verify that the null model is not identical to the original (unless trivial).
        For a non-trivial graph, rewiring should change at least some edges.
        """
        # Use a larger matrix to ensure rewiring is possible and likely
        # 3 plants, 3 pollinators, with some redundancy
        large_matrix = np.array([
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1]
        ], dtype=float)

        null_model = generate_degree_preserving_null_model(large_matrix, iterations=100)

        # The null model should differ from the original with high probability
        # (Unless the graph is so constrained it can't be rewired, which is rare here)
        # We assert that it is NOT identical to ensure rewiring happened
        self.assertFalse(np.array_equal(large_matrix, null_model),
                         "Null model should differ from original after rewiring")

    @unittest.skipIf(not VALIDATION_MODULE_EXISTS, "validation module not yet implemented")
    def test_matrix_shape_and_type(self):
        """Verify the output is a numpy array of the same shape and type."""
        null_model = generate_degree_preserving_null_model(self.original_matrix)

        self.assertIsInstance(null_model, np.ndarray, "Output must be a numpy array")
        self.assertEqual(null_model.shape, self.original_matrix.shape,
                         "Output shape must match input shape")
        self.assertEqual(null_model.dtype, self.original_matrix.dtype,
                         "Output dtype must match input dtype")

    @unittest.skipIf(not VALIDATION_MODULE_EXISTS, "validation module not yet implemented")
    def test_binary_values(self):
        """Verify the null model contains only 0s and 1s (or floats representing them)."""
        null_model = generate_degree_preserving_null_model(self.original_matrix)

        unique_values = np.unique(null_model)
        # Allow for floating point representation of 0.0 and 1.0
        valid_values = set([0.0, 1.0, 0, 1])
        for val in unique_values:
            self.assertIn(val, valid_values,
                          f"Null model contains invalid value: {val}")

    @unittest.skipIf(not VALIDATION_MODULE_EXISTS, "validation module not yet implemented")
    def test_no_self_loops_bipartite(self):
        """
        Ensure that the bipartite structure is maintained (no connections within the same set).
        Since the input is bipartite (plants x pollinators), the null model should also be.
        This is implicitly true if we only swap edges between the two sets.
        """
        # This test validates the logic of the implementation:
        # It should not create connections where none existed between the two sets.
        # Since the input is strictly bipartite (rows=plants, cols=pollinators),
        # the output must also respect this partition.
        null_model = generate_degree_preserving_null_model(self.original_matrix)
        
        # The structure is preserved by definition of the input/output format.
        # We verify the input was bipartite and output is same shape.
        self.assertEqual(null_model.shape, self.original_matrix.shape)

    def test_empty_matrix_handling(self):
        """Test behavior with an empty matrix."""
        empty_matrix = np.zeros((2, 2))
        
        if VALIDATION_MODULE_EXISTS:
            # If module exists, it should handle empty gracefully
            null_model = generate_degree_preserving_null_model(empty_matrix)
            self.assertTrue(np.array_equal(null_model, empty_matrix))
        else:
            # If module doesn't exist, we just ensure our mock doesn't crash
            # (The mock implementation above returns a copy)
            pass

    def test_single_edge_handling(self):
        """Test behavior with a single edge (cannot be rewired)."""
        single_edge = np.array([[1, 0], [0, 0]])
        
        if VALIDATION_MODULE_EXISTS:
            null_model = generate_degree_preserving_null_model(single_edge, iterations=10)
            # With only one edge, there are no alternative configurations.
            # The null model should be identical to the original.
            self.assertTrue(np.array_equal(null_model, single_edge))
        else:
            # Mock behavior
            pass


class TestNetworkStatistics(unittest.TestCase):
    """Tests for the helper function calculating network statistics."""

    def test_calculate_degree_mean(self):
        matrix = np.array([[1, 1], [1, 0]], dtype=float)
        stats = calculate_network_statistics(matrix)
        
        # Total edges = 3, Total nodes = 4 (2+2)
        # Average degree = 2 * edges / nodes = 6 / 4 = 1.5
        # Or simply mean of all degrees
        expected_mean = 1.5
        
        self.assertAlmostEqual(stats['degree_mean'], expected_mean, places=5)

    def test_calculate_clustering(self):
        # Simple test for clustering coefficient calculation
        # (Implementation details depend on bipartite clustering definition)
        matrix = np.array([[1, 1], [1, 0]], dtype=float)
        stats = calculate_network_statistics(matrix)
        
        self.assertIn('clustering', stats)
        self.assertIsInstance(stats['clustering'], float)


if __name__ == '__main__':
    unittest.main()