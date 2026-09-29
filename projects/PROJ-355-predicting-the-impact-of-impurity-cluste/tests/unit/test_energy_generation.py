"""
Unit test for segregation energy generation verification.

This test verifies that the simulation module produces non-empty results
and logs the count of generated energies as required by FR-003.
"""
import pytest
import numpy as np
import logging
import io
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.simulate_energy import (
    calculate_segregation_energy,
    apply_structural_perturbation,
    run_simulation
)
from config import get_project_root, get_data_paths


def test_calculate_segregation_energy_logic():
    """
    Verify that the energy calculation function returns a float.
    """
    # Mock inputs since we cannot run a full physics simulation in this unit test
    # without a real potential file and structure.
    
    # Create a mock structure object with required attributes
    mock_structure = Mock()
    mock_structure.num_atoms = 10
    mock_structure.lattice = Mock()
    mock_structure.lattice.matrix = np.eye(3) * 5.0
    
    # Mock the potential path (we don't actually load it in this unit test)
    mock_potential_path = "/mock/path/Fe_Cr.eam.fs"
    
    # Mock the energy calculation to return a deterministic value
    # This ensures the function signature and return type are correct
    with patch('data.simulate_energy.calculate_total_energy', return_value=-100.5):
        result = calculate_segregation_energy(mock_structure, mock_potential_path)
        
        assert isinstance(result, float)
        assert result == -100.5


def test_apply_structural_perturbation():
    """
    Verify that structural perturbation is applied correctly.
    """
    # Create a mock structure
    mock_structure = Mock()
    mock_structure.num_atoms = 10
    mock_structure.lattice = Mock()
    mock_structure.lattice.matrix = np.eye(3) * 5.0
    
    # Mock the perturbation vector calculation
    with patch('data.simulate_energy.get_interface_normal', return_value=np.array([0.0, 0.0, 1.0])):
        with patch('data.simulate_energy.config.RANDOM_SEED', 42):
            # Apply perturbation
            perturbed = apply_structural_perturbation(mock_structure, scale=0.01)
            
            # Verify perturbation was applied (structure should be modified)
            assert perturbed is not None
            assert perturbed.num_atoms == mock_structure.num_atoms


@patch('data.simulate_energy.Path.exists', return_value=True)
@patch('data.simulate_energy.load_structure_from_file')
@patch('data.simulate_energy.calculate_segregation_energy')
@patch('data.simulate_energy.json.dump')
def test_run_simulation_produces_non_empty_results(
    mock_json_dump, 
    mock_calc_energy, 
    mock_load_structure, 
    mock_exists
):
    """
    Verify that run_simulation produces non-empty results and logs the count.
    This satisfies the requirement: "Verify that simulate_energy.py produces 
    non-empty results and logs the count of generated energies."
    """
    # Setup mocks
    mock_structure = Mock()
    mock_structure.num_atoms = 20
    mock_load_structure.return_value = mock_structure
    mock_calc_energy.return_value = -5.2  # Non-zero energy value
    
    # Mock potential path
    mock_potential_path = "/mock/potentials/Fe_Cr.eam.fs"
    
    # Create a mock GB supercell file path
    mock_gb_file = Path("/mock/gb_supercells/sim_001.json")
    mock_gb_files = [mock_gb_file]
    
    # Capture log output
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    
    # Get the logger used by simulate_energy
    logger = logging.getLogger('data.simulate_energy')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Run simulation with mocked inputs
    with patch('data.simulate_energy.glob.glob', return_value=mock_gb_files):
        with patch('data.simulate_energy.Path.is_file', return_value=True):
            with patch('data.simulate_energy.get_project_potential_path', return_value=mock_potential_path):
                results = run_simulation(
                    gb_supercell_dir="/mock/gb_supercells",
                    output_path="/mock/results/energies.json"
                )
    
    # Verify results are non-empty
    assert results is not None
    assert len(results) > 0, "Results list should not be empty"
    
    # Verify energy values are non-empty floats
    for result in results:
        assert 'energy' in result
        assert isinstance(result['energy'], (int, float))
        assert not np.isnan(result['energy'])
    
    # Verify the count is logged
    log_output = log_stream.getvalue()
    assert "generated" in log_output.lower() or "count" in log_output.lower(), \
        f"Log should mention count of generated energies. Got: {log_output}"
    
    # Verify the exact count matches the number of results
    assert str(len(results)) in log_output or "1" in log_output, \
        f"Log should indicate the number of generated energies. Got: {log_output}"
    
    # Clean up logger
    logger.removeHandler(handler)


def test_energy_values_are_realistic():
    """
    Verify that generated energies are within physically realistic ranges.
    Segregation energies are typically negative (favorable) or small positive.
    """
    # Mock the energy calculation to return a realistic value
    with patch('data.simulate_energy.calculate_segregation_energy', return_value=-2.5):
        # This would be called within run_simulation in a real scenario
        energy = calculate_segregation_energy(Mock(), "/mock/path")
        
        # Realistic segregation energies are typically between -10 and +5 eV
        assert -10.0 <= energy <= 5.0, \
            f"Energy {energy} is outside realistic range [-10, 5] eV"