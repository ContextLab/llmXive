"""
Unit tests for T017: sweep_cutoff sensitivity analysis.
"""
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.sweep_cutoff import (
    build_adjacency_matrix,
    calculate_edge_feature_stability,
    analyze_cutoff,
    get_project_root
)

class TestBuildAdjacencyMatrix:
    def test_simple_triangle(self):
        # 3 atoms forming a triangle with side ~1.5 Angstroms
        # Cutoff 2.0 should connect all
        positions = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [0.0, 1.5, 0.0]
        ])
        adj = build_adjacency_matrix(positions, cutoff=2.0)
        
        # Distances: (0,1)=1.5, (0,2)=1.5, (1,2)=~2.12
        # With cutoff 2.0:
        # 0-1: True
        # 0-2: True
        # 1-2: False (2.12 > 2.0)
        
        assert adj[0, 1] == True
        assert adj[1, 0] == True
        assert adj[0, 2] == True
        assert adj[2, 0] == True
        assert adj[1, 2] == False
        assert adj[2, 1] == False
        assert np.all(np.diag(adj) == False) # No self loops

    def test_cutoff_sensitivity(self):
        positions = np.array([
            [0.0, 0.0, 0.0],
            [2.5, 0.0, 0.0]
        ])
        
        # Cutoff 2.0 -> disconnected
        adj_2 = build_adjacency_matrix(positions, cutoff=2.0)
        assert np.sum(adj_2) == 0
        
        # Cutoff 3.0 -> connected
        adj_3 = build_adjacency_matrix(positions, cutoff=3.0)
        assert np.sum(adj_3) == 2 # 0-1 and 1-0

class TestCalculateEdgeFeatureStability:
    def test_single_molecule(self):
        # Single molecule, 4 atoms in a line
        # Positions: 0, 1, 2, 3 Angstroms apart
        positions = [np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0]
        ])]
        atomic_numbers = [[6, 6, 6, 6]] # Carbon
        
        cutoffs = [1.5, 2.5]
        results = calculate_edge_feature_stability(atomic_numbers, positions, cutoffs)
        
        # Cutoff 1.5: connects 0-1, 1-2. (2-3 is 1.0? No, 2.0-3.0 is 1.0. Wait.
        # Positions: 0, 1, 2, 3.
        # Distances:
        # 0-1: 1.0 (< 1.5) -> Connected
        # 1-2: 1.0 (< 1.5) -> Connected
        # 2-3: 1.0 (< 1.5) -> Connected
        # 0-2: 2.0 (> 1.5) -> No
        # 1-3: 2.0 (> 1.5) -> No
        # Edges: (0,1), (1,0), (1,2), (2,1), (2,3), (3,2) -> 6 edges
        
        assert results[1.5]["edge_count"] == 6
        
        # Cutoff 2.5:
        # 0-2: 2.0 (< 2.5) -> Connected
        # 1-3: 2.0 (< 2.5) -> Connected
        # 0-3: 3.0 (> 2.5) -> No
        # New edges: (0,2), (2,0), (1,3), (3,1) -> 4 new
        # Total: 6 + 4 = 10
        
        assert results[2.5]["edge_count"] == 10

class TestAnalyzeCutoff:
    def test_output_structure(self):
        positions = [np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])]
        atomic_numbers = [[1, 1]]
        cutoffs = [1.5, 2.0]
        
        result = analyze_cutoff(atomic_numbers, positions, cutoffs)
        
        assert "cutoffs_tested" in result
        assert "metrics_per_cutoff" in result
        assert "stability_analysis" in result
        assert "summary" in result
        
        assert 1.5 in result["metrics_per_cutoff"]
        assert 2.0 in result["metrics_per_cutoff"]
        
        # Check stability analysis length
        assert len(result["stability_analysis"]) == 1

class TestGetProjectRoot:
    def test_returns_path(self):
        root = get_project_root()
        assert isinstance(root, Path)
        # Should be an absolute path
        assert root.is_absolute()