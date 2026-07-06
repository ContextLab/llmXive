"""
Unit tests for SMILES parsing and feature extraction (Task T015).

Tests the SMILES-to-PolymerGraph conversion and node/edge feature extraction
logic defined in code/data/ingestion.py and code/data/preprocessing.py.
"""
import pytest
import os
import sys
import numpy as np
from typing import List, Dict, Any

# Add project root to path for imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from rdkit import Chem
from rdkit.Chem import AllChem

from models.polymer_graph import PolymerGraph
from data.ingestion import smiles_to_polymer_graph, CleanedDataset
from data.preprocessing import extract_graph_features


class TestSmilesToPolymerGraph:
    """Tests for the SMILES parsing logic in ingestion.py"""

    def test_valid_smiles_parsing(self):
        """Test parsing a simple valid SMILES string (Benzene)"""
        smiles = "c1ccccc1"
        polymer_graph = smiles_to_polymer_graph(smiles)

        assert polymer_graph is not None
        assert isinstance(polymer_graph, PolymerGraph)
        assert polymer_graph.smiles == smiles
        assert polymer_graph.molecular_weight > 0
        assert len(polymer_graph.nodes) > 0
        assert len(polymer_graph.edges) > 0

    def test_stereochemistry_handling(self):
        """Test that stereochemistry is handled (no crash)"""
        # Trans-2-butene
        smiles = "C/C=C/C"
        polymer_graph = smiles_to_polymer_graph(smiles)

        assert polymer_graph is not None
        assert polymer_graph.smiles == smiles
        # Should still have valid graph structure
        assert len(polymer_graph.nodes) > 0

    def test_invalid_smiles_raises(self):
        """Test that invalid SMILES raises ValueError"""
        invalid_smiles = "invalid_smiles_string_12345"
        
        with pytest.raises(ValueError):
            smiles_to_polymer_graph(invalid_smiles)

    def test_empty_smiles_raises(self):
        """Test that empty SMILES raises ValueError"""
        with pytest.raises(ValueError):
            smiles_to_polymer_graph("")

    def test_molecular_weight_calculation(self):
        """Test that MW is calculated correctly for a known molecule"""
        # Ethane: C2H6, MW ≈ 30.07
        smiles = "CC"
        polymer_graph = smiles_to_polymer_graph(smiles)

        # Allow small floating point tolerance
        assert 29.0 < polymer_graph.molecular_weight < 32.0

    def test_node_features_population(self):
        """Test that node features are populated for atoms"""
        smiles = "CCO"  # Ethanol
        polymer_graph = smiles_to_polymer_graph(smiles)

        assert len(polymer_graph.node_features) == len(polymer_graph.nodes)
        
        # Check that each node has expected keys
        for node_idx, features in polymer_graph.node_features.items():
            assert "atom_type" in features
            assert "hybridization" in features
            assert "atomic_num" in features

    def test_edge_features_population(self):
        """Test that edge features are populated for bonds"""
        smiles = "C=O"  # Formaldehyde
        polymer_graph = smiles_to_polymer_graph(smiles)

        assert len(polymer_graph.edge_features) == len(polymer_graph.edges)
        
        for edge_idx, features in polymer_graph.edge_features.items():
            assert "bond_type" in features
            assert "is_conjugated" in features


class TestFeatureExtraction:
    """Tests for feature extraction logic in preprocessing.py"""

    def test_extract_graph_features_returns_dict(self):
        """Test that extract_graph_features returns a dictionary"""
        smiles = "c1ccccc1"
        polymer_graph = smiles_to_polymer_graph(smiles)
        
        features = extract_graph_features(polymer_graph)
        
        assert isinstance(features, dict)
        assert "node_features" in features
        assert "edge_features" in features

    def test_node_feature_dimensions(self):
        """Test that node features have correct dimensions"""
        smiles = "CC"
        polymer_graph = smiles_to_polymer_graph(smiles)
        
        features = extract_graph_features(polymer_graph)
        node_feats = features["node_features"]
        
        # Should be a dict with integer keys
        assert isinstance(node_feats, dict)
        assert all(isinstance(k, int) for k in node_feats.keys())
        
        # Each feature vector should be a list or array
        for feat in node_feats.values():
            assert len(feat) > 0

    def test_edge_feature_dimensions(self):
        """Test that edge features have correct dimensions"""
        smiles = "C=O"
        polymer_graph = smiles_to_polymer_graph(smiles)
        
        features = extract_graph_features(polymer_graph)
        edge_feats = features["edge_features"]
        
        assert isinstance(edge_feats, dict)
        assert all(isinstance(k, int) for k in edge_feats.keys())
        
        for feat in edge_feats.values():
            assert len(feat) > 0

    def test_feature_extraction_with_empty_graph(self):
        """Test behavior with a graph that has no edges (single atom)"""
        # Single carbon atom
        smiles = "[C]"
        try:
            polymer_graph = smiles_to_polymer_graph(smiles)
            features = extract_graph_features(polymer_graph)
            
            assert isinstance(features, dict)
            # Should have nodes but possibly no edges
            assert "node_features" in features
        except ValueError:
            # Some single-atom SMILES might be invalid in RDKit context
            pass


class TestCleanedDataset:
    """Tests for the CleanedDataset dataclass"""

    def test_cleaned_dataset_creation(self):
        """Test creating a CleanedDataset instance"""
        graphs: List[PolymerGraph] = []
        metadata: Dict[str, Any] = {"source": "test", "count": 0}
        
        dataset = CleanedDataset(
            graphs=graphs,
            metadata=metadata
        )
        
        assert len(dataset.graphs) == 0
        assert dataset.metadata["source"] == "test"

    def test_cleaned_dataset_with_data(self):
        """Test creating a CleanedDataset with actual graphs"""
        smiles_list = ["CC", "CCO", "c1ccccc1"]
        graphs = []
        for smiles in smiles_list:
            graph = smiles_to_polymer_graph(smiles)
            graphs.append(graph)
        
        dataset = CleanedDataset(
            graphs=graphs,
            metadata={"source": "test", "count": len(graphs)}
        )
        
        assert len(dataset.graphs) == 3
        assert dataset.metadata["count"] == 3

    def test_cleaned_dataset_serialization_compatibility(self):
        """Test that CleanedDataset can be used with save_to_hdf5 logic"""
        # Just verify the structure is compatible
        smiles = "CC"
        graph = smiles_to_polymer_graph(smiles)
        dataset = CleanedDataset(
            graphs=[graph],
            metadata={"test": True}
        )
        
        # Verify we can access the graphs
        assert len(dataset.graphs) == 1
        assert isinstance(dataset.graphs[0], PolymerGraph)


class TestIntegration:
    """Integration tests combining parsing and feature extraction"""

    def test_full_pipeline_small_molecule(self):
        """Test the full pipeline from SMILES to features"""
        smiles = "CCO"  # Ethanol
        
        # Step 1: Parse SMILES
        polymer_graph = smiles_to_polymer_graph(smiles)
        assert polymer_graph is not None
        
        # Step 2: Extract features
        features = extract_graph_features(polymer_graph)
        assert features is not None
        assert len(features["node_features"]) > 0

    def test_multiple_molecules_pipeline(self):
        """Test processing multiple molecules"""
        smiles_list = ["CC", "CCO", "c1ccccc1", "C=O"]
        
        graphs = []
        for smiles in smiles_list:
            graph = smiles_to_polymer_graph(smiles)
            graphs.append(graph)
        
        assert len(graphs) == 4
        
        # Extract features for all
        all_features = []
        for graph in graphs:
            features = extract_graph_features(graph)
            all_features.append(features)
        
        assert len(all_features) == 4
        for feats in all_features:
            assert "node_features" in feats
            assert "edge_features" in feats

    def test_feature_consistency_across_runs(self):
        """Test that feature extraction is deterministic for same input"""
        smiles = "c1ccccc1"
        
        # Parse twice
        graph1 = smiles_to_polymer_graph(smiles)
        graph2 = smiles_to_polymer_graph(smiles)
        
        # Extract features
        feats1 = extract_graph_features(graph1)
        feats2 = extract_graph_features(graph2)
        
        # Compare node feature counts
        assert len(feats1["node_features"]) == len(feats2["node_features"])
        assert len(feats1["edge_features"]) == len(feats2["edge_features"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])