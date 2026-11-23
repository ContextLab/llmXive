"""
Contract tests for the descriptor extractor module (T018).

These tests verify:
1. SMILES to adjacency conversion
2. Graph metric calculations (degree, density, clustering)
3. Output schema compliance
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.descriptor_extractor import (
    parse_smiles_to_adjacency,
    calculate_degree,
    calculate_graph_density,
    calculate_clustering_coefficient,
    extract_descriptors
)

class TestSmilesToAdjacency:
    """Tests for SMILES to adjacency matrix conversion."""

    def test_simple_ethane(self):
        """Test parsing a simple molecule (ethane)."""
        smiles = "CC"
        adj = parse_smiles_to_adjacency(smiles)
        assert adj is not None
        assert adj.shape[0] == adj.shape[1]  # Square matrix
        assert adj.shape[0] > 1  # At least 2 atoms

    def test_invalid_smiles(self):
        """Test that invalid SMILES returns None."""
        invalid_smiles = "INVALID_SMILES_123"
        adj = parse_smiles_to_adjacency(invalid_smiles)
        assert adj is None

    def test_empty_string(self):
        """Test that empty string returns None."""
        adj = parse_smiles_to_adjacency("")
        assert adj is None

    def test_none_input(self):
        """Test that None input returns None."""
        adj = parse_smiles_to_adjacency(None)
        assert adj is None

class TestGraphMetrics:
    """Tests for graph metric calculations."""

    def test_degree_calculation(self):
        """Test average degree calculation on a simple graph."""
        # Triangle graph: 3 nodes, each with degree 2
        adj = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        degree = calculate_degree(adj)
        assert degree == 2.0

    def test_density_calculation_complete(self):
        """Test density on a complete graph (density should be 1.0)."""
        # Complete graph K3
        adj = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        density = calculate_graph_density(adj)
        assert density == 1.0

    def test_density_calculation_empty(self):
        """Test density on an empty graph (density should be 0.0)."""
        adj = np.array([
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ])
        density = calculate_graph_density(adj)
        assert density == 0.0

    def test_clustering_complete_graph(self):
        """Test clustering on a complete graph (should be 1.0)."""
        adj = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        clustering = calculate_clustering_coefficient(adj)
        assert clustering == 1.0

    def test_clustering_line_graph(self):
        """Test clustering on a line graph (should be 0.0)."""
        # Line: 1-2-3
        adj = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        clustering = calculate_clustering_coefficient(adj)
        # In a line graph, no triangles exist, so clustering is 0
        assert clustering == 0.0

    def test_empty_matrix(self):
        """Test metrics on empty matrix."""
        adj = np.array([]).reshape(0, 0)
        assert calculate_degree(adj) == 0.0
        assert calculate_graph_density(adj) == 0.0
        assert calculate_clustering_coefficient(adj) == 0.0

class TestExtractDescriptors:
    """Tests for the full descriptor extraction pipeline."""

    def test_ethane_descriptors(self):
        """Test descriptor extraction for ethane."""
        degree, density, clustering = extract_descriptors("CC")
        assert isinstance(degree, float)
        assert isinstance(density, float)
        assert isinstance(clustering, float)
        assert 0 <= density <= 1.0
        assert 0 <= clustering <= 1.0

    def test_benzene_descriptors(self):
        """Test descriptor extraction for benzene (cyclic)."""
        degree, density, clustering = extract_descriptors("c1ccccc1")
        assert isinstance(degree, float)
        assert isinstance(density, float)
        assert isinstance(clustering, float)
        # Benzene has a ring, so clustering should be > 0
        assert clustering > 0.0

    def test_invalid_smiles_returns_zeros(self):
        """Test that invalid SMILES returns (0, 0, 0)."""
        degree, density, clustering = extract_descriptors("INVALID")
        assert degree == 0.0
        assert density == 0.0
        assert clustering == 0.0