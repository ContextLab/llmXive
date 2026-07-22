"""
Unit tests for descriptor_utils.py
"""
import os
import tempfile
import numpy as np
import pytest
import mdtraj as md

from code.data.descriptor_utils import (
    _calculate_rdf_descriptors,
    _calculate_bond_angle_variance,
    _calculate_coordination_numbers,
    extract_all_descriptors
)

@pytest.fixture
def dummy_trajectory():
    """Create a simple dummy trajectory for testing."""
    # Create a simple cubic box of atoms
    n_atoms = 10
    coords = np.random.rand(n_atoms, 3) * 10.0 # 10 Angstrom box
    top = md.Topology()
    chain = top.add_chain()
    res = top.add_residue("DUM", chain)
    for _ in range(n_atoms):
        top.add_atom("X", md.element.get_by_symbol("H"), res)

    traj = md.Trajectory(coords.reshape(1, n_atoms, 3), top)
    traj.unitcell_lengths = np.array([[10.0, 10.0, 10.0]])
    return traj

def test_rdf_descriptors(dummy_trajectory):
    """Test RDF descriptor calculation."""
    result = _calculate_rdf_descriptors(dummy_trajectory)
    assert isinstance(result, dict)
    assert "r_peak" in result
    assert "sigma" in result
    assert "cn_1st_shell" in result
    # With random atoms, r_peak might be small or 0, but structure should be valid
    assert isinstance(result["r_peak"], float)

def test_bond_angle_variance(dummy_trajectory):
    """Test bond angle variance calculation."""
    result = _calculate_bond_angle_variance(dummy_trajectory)
    assert isinstance(result, float)
    assert result >= 0.0

def test_coordination_numbers(dummy_trajectory):
    """Test coordination number calculation."""
    result = _calculate_coordination_numbers(dummy_trajectory, cutoff=5.0)
    assert isinstance(result, float)
    assert result >= 0.0

def test_extract_all_descriptors(tmp_path):
    """Test the full extraction pipeline."""
    # Create a temporary trajectory file
    n_atoms = 20
    coords = np.random.rand(5, n_atoms, 3) * 10.0 # 5 frames
    top = md.Topology()
    chain = top.add_chain()
    res = top.add_residue("DUM", chain)
    for _ in range(n_atoms):
        top.add_atom("X", md.element.get_by_symbol("H"), res)

    traj = md.Trajectory(coords, top)
    traj.unitcell_lengths = np.array([[10.0, 10.0, 10.0]] * 5)

    temp_file = tmp_path / "test_traj.xtc"
    traj.save(temp_file)

    result = extract_all_descriptors(str(temp_file), "test_comp_001")

    assert result["status"] == "success"
    assert result["composition_id"] == "test_comp_001"
    assert "rdf_peak_position" in result
    assert "bond_angle_variance" in result
    assert "coordination_number_fixed" in result

def test_extract_all_descriptors_missing_file(tmp_path):
    """Test handling of missing file."""
    result = extract_all_descriptors(str(tmp_path / "nonexistent.xtc"), "test_comp_001")
    assert result["status"] == "failed"
    assert "error" in result