"""
Unit tests for validation utilities.
"""
import pytest
import numpy as np
from pymatgen.core import Structure, Lattice
from utils.validation import (
    check_missing_bond_lengths,
    check_degenerate_voronoi_cells,
    validate_structure,
    validate_dataset,
    filter_valid_structures
)


def create_test_structure(
    formula="Li2O",
    lattice_params=(4.0, 4.0, 4.0),
    alpha=90, beta=90, gamma=90
):
    """Create a simple test structure."""
    lattice = Lattice.from_parameters(
        *lattice_params, alpha, beta, gamma
    )
    species = ["Li", "Li", "O"]
    coords = [
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.5],
        [0.5, 0.5, 0.0]
    ]
    return Structure(lattice, species, coords)


def test_check_missing_bond_lengths_valid():
    """Test bond length check on a valid structure."""
    structure = create_test_structure()
    has_missing, missing = check_missing_bond_lengths(structure)
    
    # For a simple structure, we expect either no missing or very few
    assert isinstance(has_missing, bool)
    assert isinstance(missing, list)


def test_check_degenerate_voronoi_cells_valid():
    """Test Voronoi cell check on a valid structure."""
    structure = create_test_structure()
    has_degenerate, degenerate = check_degenerate_voronoi_cells(structure)
    
    assert isinstance(has_degenerate, bool)
    assert isinstance(degenerate, list)


def test_validate_structure():
    """Test comprehensive structure validation."""
    structure = create_test_structure()
    result = validate_structure(structure)
    
    assert "is_valid" in result
    assert "missing_bond_count" in result
    assert "degenerate_voronoi_count" in result
    assert "issues" in result
    assert isinstance(result["is_valid"], bool)
    assert isinstance(result["missing_bond_count"], int)


def test_validate_dataset():
    """Test dataset validation returns DataFrame."""
    structures = [
        create_test_structure(),
        create_test_structure()
    ]
    
    df = validate_dataset(structures)
    
    assert isinstance(df, type(pd.DataFrame()))
    assert "structure_index" in df.columns
    assert "is_valid" in df.columns


def test_filter_valid_structures():
    """Test filtering returns only valid structures with indices."""
    structures = [
        create_test_structure(),
        create_test_structure()
    ]
    
    valid = filter_valid_structures(structures)
    
    assert isinstance(valid, list)
    for item in valid:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], Structure)
        assert isinstance(item[1], int)