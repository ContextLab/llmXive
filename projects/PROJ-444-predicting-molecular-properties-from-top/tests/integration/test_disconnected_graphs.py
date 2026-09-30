import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import logging

# Add code directory to path
project_root = Path("projects/PROJ-444-predicting-molecular-properties-from-top")
sys.path.insert(0, str(project_root / "code"))

from utils.graph_builder import build_molecular_graph, is_valid_molecule
from utils.persistence_utils import compute_persistence_diagram, handle_empty_diagram, vectorize
import networkx as nx

# Configure logging to see debug info during tests if needed
logging.basicConfig(level=logging.INFO)

def test_disconnected_graph_handling():
    """
    Test that disconnected graphs (e.g., mixtures) are handled gracefully.
    RDKit may return a graph with multiple components for mixture SMILES.
    """
    # SMILES representing a mixture (two separate molecules)
    mixture_smiles = "CCO.CC(=O)O"  # Ethanol + Acetic acid

    mol = is_valid_molecule(mixture_smiles)
    assert mol is not None, "Mixture SMILES should be valid in RDKit"

    graph = build_molecular_graph(mol)
    assert graph is not None, "Graph should be built for mixture"

    # Check if graph is disconnected
    num_components = nx.number_connected_components(graph)
    assert num_components > 1, "Mixture should produce a disconnected graph"

    # Compute persistence diagram - should handle disconnected components
    try:
        diagram = compute_persistence_diagram(graph)
        # Diagram might be empty or have features from all components
        assert isinstance(diagram, list), "Diagram should be a list"
        # If there are features, verify structure
        if len(diagram) > 0:
            for point in diagram:
                assert len(point) == 2, "Each point in diagram must have 2 values (birth, death)"
                assert point[0] <= point[1], "Birth must be <= death"
    except Exception as e:
        pytest.fail(f"Failed to compute persistence diagram for disconnected graph: {e}")

def test_empty_graph_handling():
    """Test handling of invalid molecules that result in empty graphs."""
    invalid_smiles = "invalid_smiles_string_123"
    mol = is_valid_molecule(invalid_smiles)
    assert mol is None, "Invalid SMILES should return None"

    # Should not crash when handling None
    try:
        diagram = handle_empty_diagram(None)
        assert diagram == [], "Empty diagram should return empty list"
    except Exception as e:
        pytest.fail(f"Failed to handle empty graph: {e}")

def test_single_node_graph():
    """Test handling of a molecule with only one atom (rare but possible)."""
    # RDKit typically rejects single atom molecules as invalid organic molecules
    # We test the logic flow by explicitly creating a graph with one node if possible,
    # or verifying the robustness of the diagram computation on small graphs.
    # For this test, we verify that a minimal valid graph (e.g., a single bond) works.
    smiles = "CC"  # Ethane (minimal non-trivial)
    mol = is_valid_molecule(smiles)
    assert mol is not None
    graph = build_molecular_graph(mol)
    assert graph is not None

    # Ensure the graph is connected (single component)
    assert nx.number_connected_components(graph) == 1, "Ethane should be connected"

    diagram = compute_persistence_diagram(graph)
    assert isinstance(diagram, list)
    if len(diagram) > 0:
        for point in diagram:
            assert len(point) == 2
            assert point[0] <= point[1]

def test_persistence_diagram_structure():
    """Test that persistence diagrams have the expected structure."""
    # Create a simple valid molecule
    smiles = "CCO"  # Ethanol
    mol = is_valid_molecule(smiles)
    graph = build_molecular_graph(mol)

    diagram = compute_persistence_diagram(graph)

    # Diagram should be a list of (birth, death) tuples
    assert isinstance(diagram, list), "Diagram must be a list"
    if len(diagram) > 0:
        for point in diagram:
            assert len(point) == 2, "Each point in diagram must have 2 values (birth, death)"
            assert point[0] <= point[1], "Birth must be <= death"

def test_disconnected_components_individual_features():
    """
    Verify that when a graph has multiple components, the persistence diagram
    aggregates features from all components correctly.
    """
    # A mixture of two distinct molecules
    mixture_smiles = "CC.CCO"  # Ethane + Ethanol

    mol = is_valid_molecule(mixture_smiles)
    assert mol is not None

    graph = build_molecular_graph(mol)
    assert graph is not None

    num_components = nx.number_connected_components(graph)
    assert num_components == 2, "Mixture should produce exactly 2 components"

    # Compute diagram
    diagram = compute_persistence_diagram(graph)

    # The diagram should contain features from both components.
    # While we can't easily predict exact counts without running the algorithm,
    # we verify that the result is not empty and has valid structure.
    assert isinstance(diagram, list)
    assert len(diagram) > 0, "Disconnected graph should still produce features"

    for point in diagram:
        assert len(point) == 2
        assert point[0] <= point[1]

def test_tda_vector_is_zero_for_disconnected_molecules():
    """
    Integration test for disconnected graph handling.
    Input: data/raw/test_disconnected.csv (contains known disconnected SMILES).
    Assertion: assert tda_vector == [0.0]*100 for disconnected IDs.
    Verification: Run test and confirm zero-vector output.
    
    NOTE: This test assumes that the persistence_utils.vectorize function
    returns a zero-vector when the input graph is disconnected or has no
    persistent features (empty diagram).
    """
    input_file = project_root / "data" / "raw" / "test_disconnected.csv"
    
    if not input_file.exists():
        pytest.fail(f"Input file {input_file} not found. Ensure test_disconnected.csv exists.")
    
    df = pd.read_csv(input_file)
    
    resolution = 100  # 10x10 grid flattened
    expected_zero_vector = [0.0] * resolution

    for _, row in df.iterrows():
        smiles = row['smiles']
        mol_id = row['molecule_id']
        
        mol = is_valid_molecule(smiles)
        if mol is None:
            pytest.fail(f"Invalid SMILES in test file: {smiles}")
        
        graph = build_molecular_graph(mol)
        if graph is None:
            pytest.fail(f"Failed to build graph for: {smiles}")
        
        # Check if disconnected
        num_components = nx.number_connected_components(graph)
        if num_components <= 1:
            # If the test data claims to be disconnected but isn't, fail
            pytest.fail(f"SMILES {smiles} (ID: {mol_id}) is not disconnected. Components: {num_components}")
        
        # Compute persistence diagram
        diagram = compute_persistence_diagram(graph)
        
        # Vectorize
        # If diagram is empty, vectorize should return zeros
        # If diagram is not empty, we check if the vector is zero (which implies 
        # the vectorization logic for disconnected graphs returns zeros as per spec)
        tda_vector = vectorize(diagram, resolution=10)
        
        # The task spec explicitly requires: assert tda_vector == [0.0]*100
        # This implies that for disconnected graphs, the vectorization must yield zeros.
        # We convert to list for comparison
        tda_list = tda_vector.flatten().tolist()
        
        assert tda_list == expected_zero_vector, \
            f"Expected zero vector for disconnected molecule {mol_id} ({smiles}), but got {tda_list}"
    
    # If we get here, all disconnected molecules produced zero vectors
    assert True