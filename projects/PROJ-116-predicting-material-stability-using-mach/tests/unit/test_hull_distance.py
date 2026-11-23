import pytest
import pandas as pd
import numpy as np
from pymatgen.core import Structure, Composition
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
from utils.hull_distance import calculate_hull_distance, calculate_hull_distances_batch, get_phase_diagram_entry
from utils.validation import validate_structure

def test_get_phase_diagram_entry():
    """Test creation of PDEntry from Structure and energy."""
    # Create a simple structure (LiFeO2)
    lattice = [[4, 0, 0], [0, 4, 0], [0, 0, 4]]
    species = ["Li", "Fe", "O", "O"]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25], [0.75, 0.75, 0.75]]
    structure = Structure(lattice, species, coords)
    
    entry = get_phase_diagram_entry(structure, -1.0)
    assert entry is not None
    assert entry.composition == structure.composition
    assert entry.energy == -1.0 * structure.num_sites

def test_calculate_hull_distance():
    """Test hull distance calculation."""
    # Create two structures with different energies
    lattice = [[4, 0, 0], [0, 4, 0], [0, 0, 4]]
    species = ["Li", "O"]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
    structure1 = Structure(lattice, species, coords)
    structure2 = Structure(lattice, species, coords)
    
    # Create entries with different energies
    entry1 = PDEntry(structure1.composition, -2.0 * structure1.num_sites)
    entry2 = PDEntry(structure2.composition, -1.0 * structure2.num_sites)
    
    phase_diagram = PhaseDiagram([entry1, entry2])
    
    # Calculate hull distance for structure2 (should be above hull)
    hull_dist = calculate_hull_distance(structure2, -1.0, phase_diagram)
    assert hull_dist > 0  # Should be above hull
    
    # Calculate hull distance for structure1 (should be on hull)
    hull_dist1 = calculate_hull_distance(structure1, -2.0, phase_diagram)
    assert hull_dist1 == 0  # Should be on hull

def test_calculate_hull_distances_batch():
    """Test batch hull distance calculation."""
    # Create test data
    lattice = [[4, 0, 0], [0, 4, 0], [0, 0, 4]]
    species = ["Li", "O"]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
    structure = Structure(lattice, species, coords)
    
    df = pd.DataFrame({
        'structure': [structure, structure, structure],
        'formation_energy_per_atom': [-2.0, -1.0, -1.5]
    })
    
    result_df, excluded_df = calculate_hull_distances_batch(df)
    
    # Check that we have results
    assert len(result_df) == 3
    assert 'hull_distance' in result_df.columns
    assert 'classification_status' in result_df.columns
    
    # Check that valid entries are marked as valid
    valid_count = (result_df['classification_status'] == 'valid').sum()
    assert valid_count > 0

def test_hull_distance_with_invalid_structure():
    """Test handling of invalid structures."""
    # Create a dataframe with None structure
    df = pd.DataFrame({
        'structure': [None, None],
        'formation_energy_per_atom': [-2.0, -1.0]
    })
    
    result_df, excluded_df = calculate_hull_distances_batch(df)
    
    # All entries should be excluded
    assert len(result_df) == 2
    assert (result_df['classification_status'] == 'excluded').sum() == 2

def test_hull_distance_retains_regression_entries():
    """Test that excluded entries are retained in regression analysis."""
    lattice = [[4, 0, 0], [0, 4, 0], [0, 0, 4]]
    species = ["Li", "O"]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
    structure = Structure(lattice, species, coords)
    
    df = pd.DataFrame({
        'structure': [structure, None],
        'formation_energy_per_atom': [-2.0, -1.0]
    })
    
    result_df, excluded_df = calculate_hull_distances_batch(df)
    
    # Regression dataset should have all entries
    assert len(result_df) == 2
    
    # Classification dataset should only have valid entries
    valid_count = (result_df['classification_status'] == 'valid').sum()
    assert valid_count == 1