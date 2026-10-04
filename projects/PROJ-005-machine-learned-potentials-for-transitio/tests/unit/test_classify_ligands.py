"""
Unit tests for T017c: Ligand Classification.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

# Import the module under test
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.classify_ligands import (
    classify_single_graph,
    calculate_distance_matrix,
    GROUP13_SYMBOLS,
    TARGET_METALS,
    Z_TO_SYMBOL,
    ATOMIC_NUMBERS
)

def test_classify_group13_with_boron():
    """Test that a graph with Boron near Pd is classified as Group13."""
    # Pd atomic number = 46
    # B atomic number = 5
    # Place Pd at origin, B at 2.0A
    atomic_numbers = np.array([46, 5])  # Pd, B
    coords = np.array([
        [0.0, 0.0, 0.0],  # Pd
        [2.0, 0.0, 0.0]   # B (within 2.5A)
    ])
    
    result = classify_single_graph(atomic_numbers, coords, TARGET_METALS)
    assert result == "Group13"

def test_classify_conventional_no_group13():
    """Test that a graph without B/Al/Ga near metal is Conventional."""
    # Pd (46), C (6), H (1)
    atomic_numbers = np.array([46, 6, 1])
    coords = np.array([
        [0.0, 0.0, 0.0],  # Pd
        [2.0, 0.0, 0.0],  # C
        [4.0, 0.0, 0.0]   # H (far)
    ])
    
    result = classify_single_graph(atomic_numbers, coords, TARGET_METALS)
    assert result == "Conventional"

def test_classify_group13_with_aluminum():
    """Test classification with Aluminum near Ni."""
    # Ni = 28, Al = 13
    atomic_numbers = np.array([28, 13])
    coords = np.array([
        [0.0, 0.0, 0.0],
        [2.4, 0.0, 0.0]  # Within 2.5A
    ])
    
    result = classify_single_graph(atomic_numbers, coords, TARGET_METALS)
    assert result == "Group13"

def test_classify_group13_with_gallium():
    """Test classification with Gallium near Cu."""
    # Cu = 29, Ga = 31
    atomic_numbers = np.array([29, 31])
    coords = np.array([
        [0.0, 0.0, 0.0],
        [2.49, 0.0, 0.0]  # Just within 2.5A
    ])
    
    result = classify_single_graph(atomic_numbers, coords, TARGET_METALS)
    assert result == "Group13"

def test_classify_boundary_distance():
    """Test that atom exactly at 2.5A is included."""
    # Pd (46), B (5)
    atomic_numbers = np.array([46, 5])
    coords = np.array([
        [0.0, 0.0, 0.0],
        [2.5, 0.0, 0.0]  # Exactly at threshold
    ])
    
    result = classify_single_graph(atomic_numbers, coords, TARGET_METALS)
    assert result == "Group13"

def test_classify_just_outside_boundary():
    """Test that atom just outside 2.5A is excluded."""
    atomic_numbers = np.array([46, 5])
    coords = np.array([
        [0.0, 0.0, 0.0],
        [2.51, 0.0, 0.0]  # Just outside
    ])
    
    result = classify_single_graph(atomic_numbers, coords, TARGET_METALS)
    assert result == "Conventional"

def test_classify_no_target_metal():
    """Test behavior when no target metal is present."""
    # Only Carbon atoms
    atomic_numbers = np.array([6, 6, 6])
    coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0]
    ])
    
    result = classify_single_graph(atomic_numbers, coords, TARGET_METALS)
    # Should default to Conventional
    assert result == "Conventional"

def test_distance_matrix():
    """Test distance matrix calculation."""
    coords = np.array([
        [0.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
        [0.0, 4.0, 0.0]
    ])
    
    dist_matrix = calculate_distance_matrix(coords)
    
    # Distance from 0 to 1 should be 3.0
    assert np.isclose(dist_matrix[0, 1], 3.0)
    # Distance from 0 to 2 should be 4.0
    assert np.isclose(dist_matrix[0, 2], 4.0)
    # Distance from 1 to 2 should be 5.0 (3-4-5 triangle)
    assert np.isclose(dist_matrix[1, 2], 5.0)
    # Diagonal should be 0
    assert np.isclose(dist_matrix[0, 0], 0.0)
    # Symmetric
    assert np.isclose(dist_matrix[1, 0], dist_matrix[0, 1])

def test_z_to_symbol_consistency():
    """Test that Z_TO_SYMBOL and ATOMIC_NUMBERS are consistent."""
    for symbol, z in ATOMIC_NUMBERS.items():
        assert Z_TO_SYMBOL[z] == symbol