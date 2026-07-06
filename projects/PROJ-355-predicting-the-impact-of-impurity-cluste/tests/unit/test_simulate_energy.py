"""
Unit tests for the simulation engine (T016b).
"""
import os
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from pymatgen.core import Structure, Lattice, Element

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.data.simulate_energy import (
    apply_structural_perturbation,
    get_simulation_config,
    calculate_segregation_energy,
    RANDOM_SEED
)

@pytest.fixture
def sample_structure():
    """Create a simple BCC Fe structure for testing."""
    lattice = Lattice.cubic(2.87)
    coords = [
        [0, 0, 0],
        [0.5, 0.5, 0.5]
    ]
    species = [Element("Fe"), Element("Fe")]
    struct = Structure(lattice, species, coords)
    return struct

def test_apply_structural_perturbation_deterministic(sample_structure):
    """Test that perturbation is deterministic with a fixed seed."""
    seed = 42
    mag = 0.05
    
    # Run twice
    struct1 = apply_structural_perturbation(sample_structure, mag, seed)
    struct2 = apply_structural_perturbation(sample_structure, mag, seed)
    
    # Check coordinates are identical
    coords1 = struct1.cart_coords
    coords2 = struct2.cart_coords
    
    assert np.allclose(coords1, coords2), "Perturbation should be deterministic with same seed"

def test_apply_structural_perturbation_magnitude(sample_structure):
    """Test that perturbation magnitude is within bounds."""
    seed = 42
    mag = 0.05
    
    perturbed = apply_structural_perturbation(sample_structure, mag, seed)
    
    orig_coords = sample_structure.cart_coords
    new_coords = perturbed.cart_coords
    
    diffs = np.linalg.norm(new_coords - orig_coords, axis=1)
    
    # Check that displacements are within [0, mag] (actually up to sqrt(3)*mag for vector sum, 
    # but individual components are bounded by mag)
    # The max displacement for a uniform cube of side 2*mag is sqrt(3)*mag
    max_possible = np.sqrt(3) * mag
    
    assert np.all(diffs <= max_possible * 1.001), "Displacement exceeds expected magnitude"
    assert np.all(diffs >= 0), "Displacement cannot be negative"

def test_get_simulation_config():
    """Test that config returns expected keys."""
    config = get_simulation_config()
    assert "potential_file" in config
    assert "perturbation_magnitude" in config
    assert "random_seed" in config
    assert "project_root" in config
    assert config["random_seed"] == RANDOM_SEED

@patch('code.data.simulate_energy.AseAtomsAdaptor')
@patch('code.data.simulate_energy.EAM')
def test_calculate_segregation_energy_mock(mock_eam, mock_adaptor, sample_structure, tmp_path):
    """Test energy calculation with mocked ASE components."""
    # Create a fake potential file
    pot_file = tmp_path / "fake.eam.fs"
    pot_file.write_text("fake potential")
    
    # Mock the adapter
    mock_atoms = MagicMock()
    mock_atoms.get_potential_energy.return_value = -10.5
    mock_adaptor.return_value.get_atoms.return_value = mock_atoms
    
    # Mock the calculator
    mock_calc = MagicMock()
    mock_eam.return_value = mock_calc
    mock_atoms.set_calculator = MagicMock()
    
    energy = calculate_segregation_energy(sample_structure, str(pot_file))
    
    assert energy == -10.5
    mock_atoms.set_calculator.assert_called_once()
    mock_atoms.get_potential_energy.assert_called_once()

def test_potential_file_not_found(sample_structure, tmp_path):
    """Test that FileNotFoundError is raised if potential is missing."""
    with pytest.raises(FileNotFoundError):
        calculate_segregation_energy(sample_structure, "/nonexistent/path.eam.fs")
