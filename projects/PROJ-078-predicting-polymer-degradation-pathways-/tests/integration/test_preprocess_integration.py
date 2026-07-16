"""
Integration tests for the preprocessing pipeline.
"""

import pytest
import numpy as np
from data_models import PolymerRecord
from preprocess import (
    filter_missing_environmental_data,
    smiles_to_molecular_graph,
    is_polyester,
    filter_polyesters,
    apply_edge_dropout
)

class TestPreprocessPipeline:
    """Integration tests for the full preprocessing workflow."""
    
    def test_full_filtering_pipeline(self):
        """Test the complete filtering and conversion pipeline."""
        # Create a diverse set of records
        records = [
            # Valid polyester with complete data
            PolymerRecord(
                id="pet1",
                smiles="CC(=O)Oc1ccccc1C(=O)O",
                temperature=25.0,
                ph=7.0,
                uv_exposure=100.0,
                degradation_pathway="hydrolysis"
            ),
            # Valid polyester with missing temp
            PolymerRecord(
                id="pet_missing_temp",
                smiles="CC(=O)OCCOC(=O)C",
                temperature=None,
                ph=7.0,
                uv_exposure=100.0,
                degradation_pathway="hydrolysis"
            ),
            # Non-polyester with complete data
            PolymerRecord(
                id="alkane",
                smiles="CCCCCCCC",
                temperature=25.0,
                ph=7.0,
                uv_exposure=100.0,
                degradation_pathway="thermal"
            ),
            # Valid polyester with complete data
            PolymerRecord(
                id="pbat",
                smiles="CC(=O)OCCCOC(=O)c1ccc(C(=O)O)cc1",
                temperature=30.0,
                ph=5.5,
                uv_exposure=150.0,
                degradation_pathway="photolysis"
            )
        ]
        
        # Step 1: Filter missing environmental data
        filtered_env = filter_missing_environmental_data(records)
        assert len(filtered_env) == 3  # Should exclude pet_missing_temp
        
        # Step 2: Filter polyesters
        filtered_polyesters = filter_polyesters(filtered_env)
        assert len(filtered_polyesters) == 2  # Should exclude alkane
        
        # Step 3: Convert to graphs
        graphs = []
        for record in filtered_polyesters:
            graph = smiles_to_molecular_graph(record.smiles)
            assert graph is not None
            graphs.append(graph)
        
        assert len(graphs) == 2
        
        # Step 4: Apply edge dropout
        augmented_graphs = []
        for graph in graphs:
            augmented = apply_edge_dropout(graph, dropout_rate=0.1, seed=42)
            assert augmented is not None
            augmented_graphs.append(augmented)
        
        assert len(augmented_graphs) == 2
    
    def test_edge_dropout_preserves_structure(self):
        """Test that edge dropout preserves the overall graph structure."""
        records = [
            PolymerRecord(
                id="test",
                smiles="CC(=O)Oc1ccccc1C(=O)O",
                temperature=25.0,
                ph=7.0,
                uv_exposure=100.0,
                degradation_pathway="hydrolysis"
            )
        ]
        
        filtered = filter_missing_environmental_data(records)
        filtered = filter_polyesters(filtered)
        
        assert len(filtered) == 1
        graph = smiles_to_molecular_graph(filtered[0].smiles)
        
        assert graph is not None
        original_nodes = graph.node_features.shape[0]
        original_edges = graph.edge_indices.shape[1]
        
        # Apply dropout
        dropped = apply_edge_dropout(graph, dropout_rate=0.5, seed=123)
        
        # Node count should be preserved
        assert dropped.node_features.shape[0] == original_nodes
        # Edge count should be <= original
        assert dropped.edge_indices.shape[1] <= original_edges
