"""
Unit tests for graph_builder module.

Tests graph construction from atomic configurations and sensitivity analysis
functionality.
"""
import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from graph_builder import (
    build_graph_from_atoms,
    build_graphs,
    validate_graph_connectivity,
    run_sensitivity_analysis,
    save_sensitivity_report
)
from models.atomic_config import AtomicConfiguration
from logging_config import setup_logging

@pytest.fixture
def sample_config():
    """Create a simple sample atomic configuration for testing."""
    # Create a simple cubic lattice of 8 atoms
    coords = []
    species = []
    for x in [0, 1]:
        for y in [0, 1]:
            for z in [0, 1]:
                coords.append([x * 2.35, y * 2.35, z * 2.35])  # Si bond length ~2.35 Å
                species.append("Si")
    
    return AtomicConfiguration(
        config_id="test_cubic_8",
        coordinates=np.array(coords),
        species=species,
        source="test",
        system_size=8
    )

@pytest.fixture
def sample_configs():
    """Create multiple sample configurations for testing."""
    configs = []
    
    # Config 1: Simple cubic (8 atoms)
    coords1 = []
    species1 = []
    for x in [0, 1]:
        for y in [0, 1]:
            for z in [0, 1]:
                coords1.append([x * 2.35, y * 2.35, z * 2.35])
                species1.append("Si")
    
    configs.append(AtomicConfiguration(
        config_id="test_cubic_8",
        coordinates=np.array(coords1),
        species=species1,
        source="test",
        system_size=8
    ))
    
    # Config 2: Larger random-like structure
    np.random.seed(42)
    coords2 = np.random.rand(20, 3) * 5.0
    species2 = ["Si"] * 20
    
    configs.append(AtomicConfiguration(
        config_id="test_random_20",
        coordinates=coords2,
        species=species2,
        source="test",
        system_size=20
    ))
    
    return configs

def test_build_graph_from_atoms_basic(sample_config):
    """Test basic graph construction from atomic configuration."""
    cutoff = 3.0  # Å
    G = build_graph_from_atoms(sample_config, cutoff)
    
    # Should have 8 nodes
    assert G.number_of_nodes() == 8
    
    # Should have edges (cubic lattice with 2.35 Å spacing, cutoff 3.0 should connect neighbors)
    assert G.number_of_edges() > 0
    
    # Each node should have a position attribute
    for node in G.nodes():
        assert 'position' in G.nodes[node]
        assert 'species' in G.nodes[node]

def test_build_graph_from_atoms_cutoff_effect(sample_config):
    """Test that cutoff radius affects edge count."""
    G_small = build_graph_from_atoms(sample_config, 2.0)  # Small cutoff
    G_large = build_graph_from_atoms(sample_config, 4.0)  # Large cutoff
    
    # Larger cutoff should have more or equal edges
    assert G_large.number_of_edges() >= G_small.number_of_edges()
    
    # Very small cutoff might result in no edges
    if G_small.number_of_edges() == 0:
        # Verify atoms are far enough apart
        positions = sample_config.coordinates
        min_dist = float('inf')
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dist = np.linalg.norm(positions[i] - positions[j])
                min_dist = min(min_dist, dist)
        assert min_dist >= 2.0  # Atoms are at least 2.0 Å apart

def test_build_graphs_multiple_configs(sample_configs):
    """Test building graphs for multiple configurations."""
    cutoff = 3.0
    graphs = build_graphs(sample_configs, cutoff)
    
    assert len(graphs) == 2
    assert "test_cubic_8" in graphs
    assert "test_random_20" in graphs
    
    for config_id, G in graphs.items():
        assert G.number_of_nodes() > 0

def test_validate_graph_connectivity_connected():
    """Test connectivity validation on a connected graph."""
    G = nx.complete_graph(5)  # Complete graph is always connected
    
    is_connected, largest_component = validate_graph_connectivity(G, "test_complete")
    
    assert is_connected is True
    assert len(largest_component) == 5

def test_validate_graph_connectivity_disconnected():
    """Test connectivity validation on a disconnected graph."""
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2)])  # Component 1
    G.add_edges_from([(3, 4)])  # Component 2
    
    is_connected, largest_component = validate_graph_connectivity(G, "test_disconnected")
    
    assert is_connected is False
    assert len(largest_component) == 3  # Largest component has 3 nodes

def test_run_sensitivity_analysis(sample_configs):
    """Test sensitivity analysis across multiple cutoffs."""
    cutoffs = [2.0, 3.0, 4.0]
    report = run_sensitivity_analysis(sample_configs, cutoffs)
    
    assert "cutoff_radii" in report
    assert "results" in report
    assert len(report["results"]) == len(cutoffs)
    
    for result in report["results"]:
        assert "cutoff_radius" in result
        assert "average_degree" in result
        assert "average_component_count" in result
        assert "configurations_processed" in result

def test_run_sensitivity_analysis_empty_list():
    """Test sensitivity analysis with empty config list."""
    report = run_sensitivity_analysis([], [2.8, 3.0])
    
    assert "note" in report
    assert report["note"] == "No data"

def test_save_sensitivity_report(sample_configs, tmp_path):
    """Test saving sensitivity report to file."""
    cutoffs = [2.5, 3.0]
    report = run_sensitivity_analysis(sample_configs, cutoffs)
    
    output_path = tmp_path / "test_sensitivity_report.json"
    saved_path = save_sensitivity_report(report, output_path)
    
    assert saved_path.exists()
    assert saved_path == output_path
    
    # Verify content
    with open(saved_path, 'r') as f:
        loaded_report = json.load(f)
    
    assert loaded_report["cutoff_radii"] == cutoffs
    assert len(loaded_report["results"]) == len(cutoffs)

def test_graph_node_attributes(sample_config):
    """Test that graph nodes have correct attributes."""
    G = build_graph_from_atoms(sample_config, 3.0)
    
    for node_id in G.nodes():
        # Check species
        assert 'species' in G.nodes[node_id]
        assert G.nodes[node_id]['species'] in sample_config.species
        
        # Check position
        assert 'position' in G.nodes[node_id]
        assert len(G.nodes[node_id]['position']) == 3

def test_sensitivity_analysis_degree_monotonicity(sample_configs):
    """Test that average degree generally increases with cutoff radius."""
    cutoffs = [2.0, 3.0, 4.0, 5.0]
    report = run_sensitivity_analysis(sample_configs, cutoffs)
    
    degrees = [r["average_degree"] for r in report["results"]]
    
    # Degrees should be non-decreasing (with some tolerance for numerical issues)
    for i in range(len(degrees) - 1):
        assert degrees[i] <= degrees[i + 1] + 0.001, \
            f"Degree should not decrease: {degrees[i]} -> {degrees[i+1]}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
