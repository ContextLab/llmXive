"""
Unit tests for topological descriptor calculations.
Tests ring statistics and Steinhardt Q6 parameter calculation.
"""
import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import sys
import math

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.atomic_config import AtomicConfiguration
from graph_builder import build_graph_from_atoms
from descriptors import calculate_ring_statistics, calculate_steinhardt_q6


def create_simple_lattice_2d():
    """
    Create a simple 2D square lattice (3x3) with known coordinates.
    This allows for deterministic verification of ring statistics.
    In a perfect 3x3 square lattice with nearest-neighbor cutoff,
    we expect 4 squares (rings of size 4).
    """
    # 3x3 grid, spacing 2.0 Angstroms
    # Coordinates: (0,0), (2,0), (4,0), ... (0,4), (2,4), (4,4)
    positions = []
    element = "Si"
    for x in range(3):
        for y in range(3):
            positions.append([float(x * 2.0), float(y * 2.0), 0.0])
    
    # Create AtomicConfiguration
    # We assume a large box to avoid periodic boundary complications in this simple test
    # or we explicitly set the box size.
    box_size = [6.0, 6.0, 6.0]
    
    config = AtomicConfiguration(
        config_id="test_2d_square_lattice",
        elements=[element] * 9,
        positions=np.array(positions),
        box=box_size,
        source="synthetic_test",
        timestamp="2023-01-01T00:00:00Z"
    )
    return config


def test_ring_statistics_on_square_lattice():
    """
    Test ring statistics calculation on a 3x3 square lattice.
    
    Expected Result:
    - With a cutoff radius slightly larger than the nearest neighbor distance (2.0),
      the graph forms a grid.
    - The minimal rings in a square grid are squares (4-membered rings).
    - In a 3x3 grid, there are 4 internal squares.
    - We expect the count for ring size 4 to be 4.
    """
    config = create_simple_lattice_2d()
    
    # Cutoff radius: Nearest neighbor is 2.0.
    # We set cutoff to 2.5 to ensure only nearest neighbors are connected.
    # 2.5 < sqrt(2^2 + 2^2) = 2.82 (diagonal), so no diagonals.
    cutoff = 2.5
    
    graph = build_graph_from_atoms(config, cutoff_radius=cutoff)
    
    # Calculate ring statistics
    ring_stats = calculate_ring_statistics(graph, min_ring_size=3, max_ring_size=10)
    
    # Assertions
    assert "ring_distribution" in ring_stats, "ring_distribution key missing"
    
    distribution = ring_stats["ring_distribution"]
    
    # Check that ring size 4 exists and has count 4
    # Note: The exact algorithm (e.g., using networkx.simple_cycles or a specific
    # shortest path based ring finder) might vary. We assume a standard
    # "smallest set of smallest rings" (SSSR) or similar approach where
    # a 3x3 grid yields 4 fundamental 4-membered rings.
    assert 4 in distribution, "Ring size 4 not found in distribution"
    assert distribution[4] == 4, f"Expected 4 rings of size 4, got {distribution[4]}"
    
    # Verify no other ring sizes exist in a perfect square lattice with this cutoff
    # (assuming the algorithm finds only the minimal cycles)
    for size, count in distribution.items():
        if size != 4:
            assert count == 0, f"Unexpected ring size {size} found with count {count}"
    
    # Verify total number of rings
    total_rings = sum(distribution.values())
    assert total_rings == 4, f"Total rings expected 4, got {total_rings}"


def test_ring_statistics_empty_graph():
    """Test ring statistics on a graph with no edges."""
    config = AtomicConfiguration(
        config_id="test_isolated_atoms",
        elements=["Si", "Si"],
        positions=np.array([[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]]),
        box=[20.0, 20.0, 20.0],
        source="synthetic_test",
        timestamp="2023-01-01T00:00:00Z"
    )
    
    # Cutoff too small to connect atoms
    graph = build_graph_from_atoms(config, cutoff_radius=1.0)
    
    ring_stats = calculate_ring_statistics(graph, min_ring_size=3, max_ring_size=10)
    
    assert ring_stats["ring_distribution"] == {}, "Expected empty distribution for no rings"


def test_ring_statistics_triangle():
    """
    Test ring statistics on a simple triangle (3 atoms).
    """
    # Equilateral triangle side length 2.0
    # (0,0), (2,0), (1, sqrt(3))
    h = math.sqrt(3)
    positions = [
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [1.0, h, 0.0]
    ]
    
    config = AtomicConfiguration(
        config_id="test_triangle",
        elements=["Si", "Si", "Si"],
        positions=np.array(positions),
        box=[10.0, 10.0, 10.0],
        source="synthetic_test",
        timestamp="2023-01-01T00:00:00Z"
    )
    
    # Cutoff > 2.0 to connect all
    graph = build_graph_from_atoms(config, cutoff_radius=2.1)
    
    ring_stats = calculate_ring_statistics(graph, min_ring_size=3, max_ring_size=10)
    
    # A triangle is a 3-membered ring
    assert 3 in ring_stats["ring_distribution"], "Ring size 3 not found"
    assert ring_stats["ring_distribution"][3] == 1, "Expected 1 ring of size 3"


def create_fcc_lattice():
    """
    Create a small FCC lattice of Silicon atoms.
    FCC is highly symmetric and should yield a high Q6 value.
    """
    # FCC unit cell side length a = 5.43 Angstroms (approx for Si)
    a = 5.43
    positions = []
    # Basis: (0,0,0), (0.5, 0.5, 0), (0.5, 0, 0.5), (0, 0.5, 0.5)
    basis = [
        (0, 0, 0),
        (0.5, 0.5, 0),
        (0.5, 0, 0.5),
        (0, 0.5, 0.5)
    ]
    
    # Create a 2x2x2 supercell
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for bx, by, bz in basis:
                    x = (i + bx) * a
                    y = (j + by) * a
                    z = (k + bz) * a
                    positions.append([x, y, z])
    
    box_size = [4.0 * a, 4.0 * a, 4.0 * a]
    
    config = AtomicConfiguration(
        config_id="test_fcc_silicon",
        elements=["Si"] * len(positions),
        positions=np.array(positions),
        box=box_size,
        source="synthetic_test",
        timestamp="2023-01-01T00:00:00Z"
    )
    return config


def create_amorphous_structure():
    """
    Create a disordered structure with low symmetry.
    This should yield a significantly lower Q6 value than FCC.
    """
    # Random positions in a box
    np.random.seed(42) # Reproducibility
    n_atoms = 64
    box_size = 10.0
    positions = np.random.rand(n_atoms, 3) * box_size
    
    config = AtomicConfiguration(
        config_id="test_amorphous_random",
        elements=["Si"] * n_atoms,
        positions=positions,
        box=[box_size, box_size, box_size],
        source="synthetic_test",
        timestamp="2023-01-01T00:00:00Z"
    )
    return config


def test_steinhardt_q6_fcc_lattice():
    """
    Test Steinhardt Q6 parameter calculation on an FCC lattice.
    
    Expected Result:
    - FCC structure has high orientational order.
    - Q6 should be significantly greater than 0 (typically ~0.57 for ideal FCC).
    """
    config = create_fcc_lattice()
    
    # Cutoff radius for Si: nearest neighbor in FCC is a * sqrt(2) / 2
    # a = 5.43 -> NN ~ 3.84 A. Set cutoff to 4.5 to capture nearest neighbors.
    cutoff = 4.5
    
    q6 = calculate_steinhardt_q6(config, cutoff_radius=cutoff)
    
    # Q6 is a scalar between 0 and 1
    assert isinstance(q6, float), "Q6 should be a float"
    assert 0.0 <= q6 <= 1.0, f"Q6 {q6} out of bounds [0, 1]"
    
    # For FCC, Q6 should be high (theoretical max for perfect crystal is ~0.57)
    # We assert it's significantly above 0.2 to distinguish from random
    assert q6 > 0.2, f"FCC Q6 {q6} is too low; expected high order."


def test_steinhardt_q6_amorphous():
    """
    Test Steinhardt Q6 parameter calculation on a random amorphous structure.
    
    Expected Result:
    - Random structure has low orientational order.
    - Q6 should be low (typically < 0.1-0.15).
    """
    config = create_amorphous_structure()
    
    # Cutoff radius: random structure, use a standard value like 3.5 A
    cutoff = 3.5
    
    q6 = calculate_steinhardt_q6(config, cutoff_radius=cutoff)
    
    # Q6 is a scalar between 0 and 1
    assert isinstance(q6, float), "Q6 should be a float"
    assert 0.0 <= q6 <= 1.0, f"Q6 {q6} out of bounds [0, 1]"
    
    # For random structure, Q6 should be low
    # We assert it's significantly lower than the FCC case
    assert q6 < 0.2, f"Random Q6 {q6} is too high; expected low order."


def test_steinhardt_q6_single_atom():
    """
    Test Steinhardt Q6 on a single atom (edge case).
    Should return 0.0 as there are no neighbors to define bonds.
    """
    config = AtomicConfiguration(
        config_id="test_single_atom",
        elements=["Si"],
        positions=np.array([[0.0, 0.0, 0.0]]),
        box=[10.0, 10.0, 10.0],
        source="synthetic_test",
        timestamp="2023-01-01T00:00:00Z"
    )
    
    cutoff = 5.0
    q6 = calculate_steinhardt_q6(config, cutoff_radius=cutoff)
    
    # No neighbors -> Q6 is undefined or 0.0. We expect 0.0.
    assert q6 == 0.0, f"Single atom Q6 should be 0.0, got {q6}"