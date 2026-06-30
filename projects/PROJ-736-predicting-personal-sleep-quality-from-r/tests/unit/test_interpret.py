"""
Unit tests for the interpretation module.
"""
import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

from modeling.interpret import (
    extract_nonzero_edges,
    map_edges_to_coordinates,
    run_interpretation
)


class TestExtractNonzeroEdges:
    """Tests for extract_nonzero_edges function."""
    
    def test_extract_nonzero_basic(self):
        """Test basic extraction of non-zero edges."""
        coefficients = np.array([0.5, -0.3, 0.0, 0.2, -0.1, 0.0])
        feature_names = [
            'node_0_node_1',
            'node_0_node_2',
            'node_0_node_3',
            'node_1_node_2',
            'node_1_node_3',
            'node_2_node_3'
        ]
        
        edges = extract_nonzero_edges(coefficients, feature_names, threshold=0.0)
        
        assert len(edges) == 4  # 4 non-zero coefficients
        assert edges[0]['node_i'] == 0
        assert edges[0]['node_j'] == 1
        assert edges[0]['coefficient'] == 0.5
        assert edges[0]['direction'] == 'positive'
        
    def test_extract_nonzero_with_threshold(self):
        """Test extraction with threshold filtering."""
        coefficients = np.array([0.5, -0.3, 0.0, 0.05, -0.1, 0.0])
        feature_names = [
            'node_0_node_1',
            'node_0_node_2',
            'node_0_node_3',
            'node_1_node_2',
            'node_1_node_3',
            'node_2_node_3'
        ]
        
        edges = extract_nonzero_edges(coefficients, feature_names, threshold=0.2)
        
        assert len(edges) == 2  # Only coefficients > 0.2
        assert abs(edges[0]['coefficient']) > 0.2
        assert abs(edges[1]['coefficient']) > 0.2
        
    def test_extract_sorted_by_abs_coefficient(self):
        """Test that edges are sorted by absolute coefficient value."""
        coefficients = np.array([0.1, -0.5, 0.3, 0.0])
        feature_names = [
            'node_0_node_1',
            'node_0_node_2',
            'node_0_node_3',
            'node_1_node_2'
        ]
        
        edges = extract_nonzero_edges(coefficients, feature_names, threshold=0.0)
        
        # Should be sorted: 0.5, 0.3, 0.1
        assert edges[0]['abs_coefficient'] >= edges[1]['abs_coefficient']
        assert edges[1]['abs_coefficient'] >= edges[2]['abs_coefficient']
        
    def test_empty_coefficients(self):
        """Test with all zero coefficients."""
        coefficients = np.array([0.0, 0.0, 0.0])
        feature_names = ['node_0_node_1', 'node_0_node_2', 'node_1_node_2']
        
        edges = extract_nonzero_edges(coefficients, feature_names, threshold=0.0)
        
        assert len(edges) == 0
        
    def test_invalid_feature_name(self):
        """Test handling of invalid feature names."""
        coefficients = np.array([0.5, 0.3, 0.2])
        feature_names = [
            'node_0_node_1',
            'invalid_format',
            'node_1_node_2'
        ]
        
        edges = extract_nonzero_edges(coefficients, feature_names, threshold=0.0)
        
        # Should skip invalid format but include valid ones
        assert len(edges) == 2
        assert 'invalid_format' not in [f"node_{e['node_i']}_node_{e['node_j']}" for e in edges]


class TestMapEdgesToCoordinates:
    """Tests for map_edges_to_coordinates function."""
    
    def test_basic_mapping(self):
        """Test basic coordinate mapping."""
        edges = [
            {'node_i': 0, 'node_j': 1, 'coefficient': 0.5},
            {'node_i': 1, 'node_j': 2, 'coefficient': -0.3}
        ]
        atlas_coords = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0]
        ])
        
        mapped_edges = map_edges_to_coordinates(edges, atlas_coords)
        
        assert len(mapped_edges) == 2
        assert mapped_edges[0]['coord_i'] == [0.0, 0.0, 0.0]
        assert mapped_edges[0]['coord_j'] == [1.0, 1.0, 1.0]
        assert mapped_edges[1]['coord_i'] == [1.0, 1.0, 1.0]
        assert mapped_edges[1]['coord_j'] == [2.0, 2.0, 2.0]
        
    def test_out_of_bounds_nodes(self):
        """Test handling of out-of-bounds node indices."""
        edges = [
            {'node_i': 0, 'node_j': 1, 'coefficient': 0.5},
            {'node_i': 10, 'node_j': 11, 'coefficient': -0.3}  # Out of bounds
        ]
        atlas_coords = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0]
        ])
        
        mapped_edges = map_edges_to_coordinates(edges, atlas_coords)
        
        # Should skip out-of-bounds edge
        assert len(mapped_edges) == 1
        assert mapped_edges[0]['node_i'] == 0


class TestRunInterpretation:
    """Tests for the main run_interpretation function."""
    
    def test_full_pipeline(self):
        """Test the full interpretation pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            model_path = Path(tmpdir) / 'model.npz'
            feature_names_path = Path(tmpdir) / 'feature_names.npy'
            atlas_coords_path = Path(tmpdir) / 'atlas_coords.npy'
            output_path = Path(tmpdir) / 'output.json'
            
            # Save model coefficients
            np.savez(model_path, coefficients=np.array([0.5, -0.3, 0.0, 0.2]), intercept=0.0)
            
            # Save feature names
            np.save(feature_names_path, np.array([
                'node_0_node_1', 'node_0_node_2', 'node_0_node_3', 'node_1_node_2'
            ]))
            
            # Save atlas coordinates
            np.save(atlas_coords_path, np.array([
                [0.0, 0.0, 0.0],
                [1.0, 1.0, 1.0],
                [2.0, 2.0, 2.0],
                [3.0, 3.0, 3.0]
            ]))
            
            # Run interpretation
            edges = run_interpretation(
                model_path=str(model_path),
                feature_names_path=str(feature_names_path),
                atlas_coords_path=str(atlas_coords_path),
                output_path=str(output_path)
            )
            
            # Verify results
            assert len(edges) == 3  # 3 non-zero coefficients
            assert output_path.exists()
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                saved_edges = json.load(f)
            assert len(saved_edges) == 3
            
    def test_with_top_n(self):
        """Test interpretation with top_n filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / 'model.npz'
            feature_names_path = Path(tmpdir) / 'feature_names.npy'
            atlas_coords_path = Path(tmpdir) / 'atlas_coords.npy'
            output_path = Path(tmpdir) / 'output.json'
            
            # Create 10 edges with decreasing coefficients
            coefficients = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
            feature_names = [f'node_0_node_{i}' for i in range(1, 11)]
            atlas_coords = np.array([[i, i, i] for i in range(11)])
            
            np.savez(model_path, coefficients=coefficients, intercept=0.0)
            np.save(feature_names_path, np.array(feature_names))
            np.save(atlas_coords_path, atlas_coords)
            
            edges = run_interpretation(
                model_path=str(model_path),
                feature_names_path=str(feature_names_path),
                atlas_coords_path=str(atlas_coords_path),
                output_path=str(output_path),
                top_n=3
            )
            
            assert len(edges) == 3
            assert edges[0]['coefficient'] == 0.9
            assert edges[1]['coefficient'] == 0.8
            assert edges[2]['coefficient'] == 0.7