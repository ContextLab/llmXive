import pytest
import networkx as nx
from code.utils.graph_builder import build_graph, validate_graph

class TestGraphBuilder:
    """Unit tests for molecular graph construction and validation."""

    def test_valid_molecule_returns_graph(self):
        """Test that valid SMILES returns a non-None graph."""
        smiles = "CCO"  # Ethanol
        graph = build_graph(smiles)
        
        assert graph is not None
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() > 0
        assert graph.number_of_edges() > 0

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None."""
        invalid_smiles = ["invalid_smiles", "C@#$", "12345"]
        
        for smiles in invalid_smiles:
            graph = build_graph(smiles)
            assert graph is None, f"Expected None for invalid SMILES: {smiles}"

    def test_benzene_ring_detection(self):
        """Test that aromatic rings are correctly detected."""
        smiles = "c1ccccc1"  # Benzene
        graph = build_graph(smiles)
        
        assert graph is not None
        assert graph.number_of_nodes() == 6
        assert graph.number_of_edges() == 6
        
        # Validate graph passes all checks
        assert validate_graph(graph) is True

    def test_valence_check_fails_invalid(self):
        """Test that valence violations are caught."""
        # Create a graph with an impossible carbon (5 bonds)
        G = nx.Graph()
        G.add_node(0, symbol='C', atomic_num=6, is_aromatic=False)
        G.add_node(1, symbol='H', atomic_num=1, is_aromatic=False)
        G.add_node(2, symbol='H', atomic_num=1, is_aromatic=False)
        G.add_node(3, symbol='H', atomic_num=1, is_aromatic=False)
        G.add_node(4, symbol='H', atomic_num=1, is_aromatic=False)
        G.add_node(5, symbol='H', atomic_num=1, is_aromatic=False)
        
        G.add_edge(0, 1, order='SINGLE')
        G.add_edge(0, 2, order='SINGLE')
        G.add_edge(0, 3, order='SINGLE')
        G.add_edge(0, 4, order='SINGLE')
        G.add_edge(0, 5, order='SINGLE')  # 5 bonds to carbon - invalid
        
        assert validate_graph(G) is False

    def test_bond_order_validation(self):
        """Test that invalid bond orders are rejected."""
        G = nx.Graph()
        G.add_node(0, symbol='C', atomic_num=6, is_aromatic=False)
        G.add_node(1, symbol='C', atomic_num=6, is_aromatic=False)
        
        # Invalid bond order
        G.add_edge(0, 1, order='INVALID')
        
        assert validate_graph(G) is False

    def test_aromaticity_check(self):
        """Test aromatic atom validation."""
        G = nx.Graph()
        G.add_node(0, symbol='C', atomic_num=6, is_aromatic=True)
        # Aromatic atom with only 1 neighbor - invalid
        G.add_node(1, symbol='H', atomic_num=1, is_aromatic=False)
        G.add_edge(0, 1, order='SINGLE')
        
        assert validate_graph(G) is False

    def test_empty_graph_validation(self):
        """Test that empty graphs are rejected."""
        G = nx.Graph()
        assert validate_graph(G) is False
        
        assert validate_graph(None) is False

    def test_triple_bond(self):
        """Test triple bond handling."""
        smiles = "C#N"  # Hydrogen cyanide
        graph = build_graph(smiles)
        
        assert graph is not None
        assert validate_graph(graph) is True

    def test_double_bond(self):
        """Test double bond handling."""
        smiles = "C=O"  # Formaldehyde
        graph = build_graph(smiles)
        
        assert graph is not None
        assert validate_graph(graph) is True