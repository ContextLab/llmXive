"""
Unit tests for molecular graph construction utilities.
"""
import pytest
import numpy as np
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.graph_utils import (
    smiles_to_molecule,
    get_node_features,
    get_edge_features,
    smiles_to_graph,
    batch_smiles_to_graphs,
    validate_graph,
    get_feature_dimensions
)

class TestSmilesToMolecule:
    """Tests for SMILES to molecule conversion."""
    
    def test_valid_ethanol(self):
        """Test valid ethanol SMILES."""
        mol = smiles_to_molecule("CCO")
        assert mol is not None
        assert mol.GetNumAtoms() == 3
    
    def test_valid_benzene(self):
        """Test valid benzene SMILES."""
        mol = smiles_to_molecule("c1ccccc1")
        assert mol is not None
        assert mol.GetNumAtoms() == 6
    
    def test_invalid_smiles(self):
        """Test invalid SMILES returns None."""
        mol = smiles_to_molecule("invalid_smiles_string")
        assert mol is None
    
    def test_empty_string(self):
        """Test empty string returns None."""
        mol = smiles_to_molecule("")
        assert mol is None

class TestGetNodeFeatures:
    """Tests for node feature extraction."""
    
    def test_ethanol_features(self):
        """Test node features for ethanol."""
        mol = smiles_to_molecule("CCO")
        features = get_node_features(mol)
        
        assert features.shape[0] == 3  # 3 atoms
        assert features.shape[1] == 3  # 3 features per atom
        assert features.dtype == np.float32
        
        # First atom is Carbon (atomic number 6)
        assert features[0][0] == 6.0
        
        # Second atom is Carbon (atomic number 6)
        assert features[1][0] == 6.0
        
        # Third atom is Oxygen (atomic number 8)
        assert features[2][0] == 8.0
    
    def test_benzene_features(self):
        """Test node features for benzene."""
        mol = smiles_to_molecule("c1ccccc1")
        features = get_node_features(mol)
        
        assert features.shape[0] == 6  # 6 atoms
        assert features.shape[1] == 3  # 3 features per atom

class TestGetEdgeFeatures:
    """Tests for edge feature extraction."""
    
    def test_ethanol_edges(self):
        """Test edge features for ethanol."""
        mol = smiles_to_molecule("CCO")
        edges = get_edge_features(mol)
        
        # Ethanol has 2 bonds: C-C and C-O
        assert edges.shape[0] == 2
        assert edges.shape[1] == 4  # 4 features per edge
        assert edges.dtype == np.float32
        
        # Check bond types are encoded (0 for single)
        assert edges[0][2] == 0.0  # First bond is single
        assert edges[1][2] == 0.0  # Second bond is single
    
    def test_benzene_edges(self):
        """Test edge features for benzene."""
        mol = smiles_to_molecule("c1ccccc1")
        edges = get_edge_features(mol)
        
        # Benzene has 6 bonds (aromatic)
        assert edges.shape[0] == 6
        # Aromatic bonds should be encoded as 3
        assert np.all(edges[:, 2] == 3.0)

class TestSmilesToGraph:
    """Tests for complete graph conversion."""
    
    def test_valid_graph_structure(self):
        """Test that a valid graph has correct structure."""
        graph = smiles_to_graph("CCO")
        
        assert graph is not None
        assert "smiles" in graph
        assert "nodes" in graph
        assert "edges" in graph
        assert graph["smiles"] == "CCO"
        assert isinstance(graph["nodes"], np.ndarray)
        assert isinstance(graph["edges"], np.ndarray)
    
    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None."""
        graph = smiles_to_graph("invalid")
        assert graph is None

class TestBatchSmilesToGraphs:
    """Tests for batch graph conversion."""
    
    def test_batch_processing(self):
        """Test batch processing of multiple SMILES."""
        smiles_list = ["CCO", "c1ccccc1", "invalid"]
        graphs = batch_smiles_to_graphs(smiles_list)
        
        assert len(graphs) == 3
        assert graphs[0] is not None
        assert graphs[1] is not None
        assert graphs[2] is None  # Invalid SMILES
    
    def test_empty_list(self):
        """Test empty list returns empty list."""
        graphs = batch_smiles_to_graphs([])
        assert graphs == []

class TestValidateGraph:
    """Tests for graph validation."""
    
    def test_valid_graph(self):
        """Test validation of a valid graph."""
        graph = smiles_to_graph("CCO")
        assert validate_graph(graph) is True
    
    def test_missing_keys(self):
        """Test validation with missing keys."""
        invalid_graph = {"smiles": "CCO", "nodes": np.array([[1, 2, 3]])}
        assert validate_graph(invalid_graph) is False
    
    def test_wrong_node_type(self):
        """Test validation with wrong node type."""
        invalid_graph = {
            "smiles": "CCO",
            "nodes": [[1, 2, 3]],  # List instead of ndarray
            "edges": np.array([[0, 1, 0, 0]])
        }
        assert validate_graph(invalid_graph) is False
    
    def test_wrong_node_dimension(self):
        """Test validation with wrong node dimension."""
        invalid_graph = {
            "smiles": "CCO",
            "nodes": np.array([1, 2, 3]),  # 1D instead of 2D
            "edges": np.array([[0, 1, 0, 0]])
        }
        assert validate_graph(invalid_graph) is False

class TestGetFeatureDimensions:
    """Tests for feature dimension utility."""
    
    def test_dimensions(self):
        """Test that feature dimensions are correct."""
        dims = get_feature_dimensions()
        
        assert "node_features" in dims
        assert "edge_features" in dims
        assert dims["node_features"] == 3
        assert dims["edge_features"] == 4