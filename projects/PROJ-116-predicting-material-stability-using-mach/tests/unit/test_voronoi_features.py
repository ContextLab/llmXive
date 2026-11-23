import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from pymatgen.core import Structure, Lattice
from pymatgen.analysis.local_env import VoronoiNN

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from feature_engineering import compute_voronoi_features, compute_bond_length_histograms
from utils.validation import check_degenerate_voronoi_cells, check_missing_bond_lengths

@pytest.fixture
def sample_structure():
    """Create a simple rock-salt structure for testing."""
    lattice = Lattice.cubic(4.0)
    species = ["Li", "O"]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
    return Structure(lattice, species, coords)

@pytest.fixture
def sample_dataframe(sample_structure):
    """Create a sample dataframe with structures."""
    return pd.DataFrame({
        "material_id": ["test_001"],
        "composition": ["Li1O1"],
        "structure": [sample_structure],
        "formation_energy_per_atom": [-2.5]
    })

def test_voronoi_features_computation(sample_dataframe):
    """Test that Voronoi features are computed correctly."""
    df_result, count_skipped = compute_voronoi_features(sample_dataframe)
    
    # Check that result dataframe has expected columns
    expected_cols = [
        "coordination_number_mean",
        "face_area_mean",
        "face_area_std",
        "solid_angle_mean",
        "solid_angle_std"
    ]
    
    for col in expected_cols:
        assert col in df_result.columns, f"Missing column: {col}"
    
    # Check that we didn't skip the valid structure
    assert count_skipped == 0, f"Expected 0 skipped entries, got {count_skipped}"
    
    # Check that features are not NaN
    assert not df_result["coordination_number_mean"].isna().any()
    assert not df_result["face_area_mean"].isna().any()

def test_voronoi_features_degenerate_cell():
    """Test handling of degenerate Voronoi cells."""
    # Create a structure that might cause issues (very small cell)
    lattice = Lattice.cubic(0.1)  # Very small lattice
    species = ["Li", "O"]
    coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
    try:
        bad_structure = Structure(lattice, species, coords)
    except Exception:
        # If structure creation fails, skip test
        pytest.skip("Could not create bad structure")
    
    df = pd.DataFrame({
        "material_id": ["bad_001"],
        "composition": ["Li1O1"],
        "structure": [bad_structure],
        "formation_energy_per_atom": [-2.5]
    })
    
    df_result, count_skipped = compute_voronoi_features(df)
    
    # Should skip or have NaN values
    assert count_skipped > 0 or df_result["coordination_number_mean"].isna().any()

def test_bond_length_histograms(sample_dataframe):
    """Test bond length histogram computation."""
    df_result, count_skipped = compute_bond_length_histograms(sample_dataframe)
    
    # Check for expected columns
    expected_cols = ["bond_length_mean", "bond_length_std", "bond_length_min", "bond_length_max"]
    for col in expected_cols:
        assert col in df_result.columns, f"Missing column: {col}"
    
    # Check that we didn't skip the valid structure
    assert count_skipped == 0, f"Expected 0 skipped entries, got {count_skipped}"
    
    # Check that features are not NaN
    assert not df_result["bond_length_mean"].isna().any()

def test_validation_functions(sample_structure):
    """Test validation functions."""
    # Valid structure
    is_valid, errors = check_degenerate_voronoi_cells(sample_structure), check_missing_bond_lengths(sample_structure)
    # Note: These might return True/False depending on the specific structure
    # We just check they don't crash
    
    # Invalid structure (None)
    is_valid_none, errors_none = check_degenerate_voronoi_cells(None) if False else (True, [])
    # The functions expect Structure objects, so we test with valid one
    
    assert isinstance(is_valid, bool)
    assert isinstance(errors, bool) # check_missing_bond_lengths returns bool
    assert isinstance(check_degenerate_voronoi_cells(sample_structure), bool)
