"""
Unit tests for the segregation energy simulation engine.
"""

import pytest
import numpy as np
from pathlib import Path
from pymatgen.core import Structure, Lattice

from code.data.simulate_energy import (
    get_simulation_config,
    apply_structural_perturbation,
    calculate_segregation_energy,
    run_simulation
)
from code.config import get_project_root

@pytest.fixture
def sample_structure():
    """Create a simple FCC Fe structure for testing."""
    lattice = Lattice.cubic(2.86) # Fe lattice constant approx
    coords = [
        [0, 0, 0],
        [0.5, 0.5, 0],
        [0.5, 0, 0.5],
        [0, 0.5, 0.5]
    ]
    species = ["Fe"] * 4
    return Structure(lattice, species, coords)

def test_get_simulation_config():
    """Test that config retrieval works."""
    config = get_simulation_config()
    assert "perturbation_magnitude" in config
    assert "random_seed" in config
    assert isinstance(config["perturbation_magnitude"], float)
    assert isinstance(config["random_seed"], int)

def test_apply_structural_perturbation_deterministic(sample_structure):
    """Test that perturbation is deterministic with a fixed seed."""
    mag = 0.01
    seed = 42
    
    # Apply twice
    p1 = apply_structural_perturbation(sample_structure, mag, seed)
    p2 = apply_structural_perturbation(sample_structure, mag, seed)
    
    # Check coordinates are identical
    coords1 = p1.cartesian_coords
    coords2 = p2.cartesian_coords
    assert np.allclose(coords1, coords2), "Perturbation should be deterministic with fixed seed"
    
    # Check that coordinates changed from original
    orig_coords = sample_structure.cartesian_coords
    assert not np.allclose(coords1, orig_coords), "Coordinates should be perturbed"

def test_apply_structural_perturbation_randomness(sample_structure):
    """Test that different seeds produce different results."""
    mag = 0.01
    p1 = apply_structural_perturbation(sample_structure, mag, seed=42)
    p2 = apply_structural_perturbation(sample_structure, mag, seed=123)
    
    assert not np.allclose(p1.cartesian_coords, p2.cartesian_coords), "Different seeds should yield different perturbations"

def test_calculate_segregation_energy(sample_structure):
    """Test energy calculation with EMT."""
    # Create a perturbed structure
    perturbed = apply_structural_perturbation(sample_structure, 0.01, 42)
    ref_energy = -10.0 # Arbitrary reference
    
    seg_energy = calculate_segregation_energy(perturbed, ref_energy)
    
    assert isinstance(seg_energy, float)
    # EMT energy for 4 Fe atoms is typically small negative
    # E_seg = E_total - ref
    # We just check it runs and returns a number
    assert np.isfinite(seg_energy)

def test_run_simulation_empty_input(tmp_path):
    """Test run_simulation with empty input list."""
    output_path = tmp_path / "test_empty.csv"
    run_simulation([], output_path)
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 0
    assert list(df.columns) == ['bulk_config_id', 'impurity_species', 'segregation_energy', 'calculation_status']

def test_run_simulation_success(tmp_path, sample_structure):
    """Test run_simulation with valid data."""
    import pandas as pd
    
    data = [{
        'structure': sample_structure,
        'bulk_config_id': 'test_001',
        'impurity_species': 'Cr',
        'reference_energy': 0.0
    }]
    
    output_path = tmp_path / "test_success.csv"
    run_simulation(data, output_path)
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 1
    assert df.iloc[0]['bulk_config_id'] == 'test_001'
    assert df.iloc[0]['calculation_status'] == 'SUCCESS'
    assert np.isfinite(df.iloc[0]['segregation_energy'])