"""
Unit tests for Hückel resonance energy calculation.
Validates that the computed resonance energy for benzene is positive and within expected range,
and for cyclohexane is near zero.
"""
import pytest
import numpy as np
from rdkit import Chem
from code.descriptors import compute_huckel_resonance_energy

def test_benzene_resonance_energy():
    """
    Test that benzene yields a positive resonance energy consistent with literature values.
    Expected: > 0.5 beta units (approx. 100 kcal/mol using 200 kcal/mol per beta scaling).
    """
    benzene_smiles = "c1ccccc1"
    mol = Chem.MolFromSmiles(benzene_smiles)
    assert mol is not None, "Failed to parse benzene SMILES"

    resonance_energy = compute_huckel_resonance_energy(mol)

    # Resonance energy should be positive (delocalization stabilizes the system)
    assert resonance_energy > 0, f"Benzene resonance energy should be positive, got {resonance_energy}"
    
    # Should be within expected range (> 0.5 beta units)
    # Literature value is approx 2 beta units (400 kcal/mol with 200 scaling)
    # We use a conservative lower bound of 0.5 beta units (100 kcal/mol)
    assert resonance_energy > 100, f"Benzene resonance energy should be > 100 kcal/mol, got {resonance_energy}"

def test_cyclohexane_resonance_energy():
    """
    Test that cyclohexane yields near-zero resonance energy (no conjugated pi system).
    Expected: close to 0 (within 1 kcal/mol tolerance).
    """
    cyclohexane_smiles = "C1CCCCC1"
    mol = Chem.MolFromSmiles(cyclohexane_smiles)
    assert mol is not None, "Failed to parse cyclohexane SMILES"

    resonance_energy = compute_huckel_resonance_energy(mol)

    # Cyclohexane has no pi system, so resonance energy should be near zero
    assert np.isclose(resonance_energy, 0.0, atol=1.0), \
        f"Cyclohexane resonance energy should be near zero, got {resonance_energy}"

def test_butadiene_resonance_energy():
    """
    Test that butadiene (conjugated system) yields positive resonance energy.
    Expected: > 0 (smaller than benzene but still positive).
    """
    butadiene_smiles = "C=CC=C"
    mol = Chem.MolFromSmiles(butadiene_smiles)
    assert mol is not None, "Failed to parse butadiene SMILES"

    resonance_energy = compute_huckel_resonance_energy(mol)

    # Butadiene has a conjugated pi system, so resonance energy should be positive
    assert resonance_energy > 0, f"Butadiene resonance energy should be positive, got {resonance_energy}"

def test_ethane_resonance_energy():
    """
    Test that ethane (no pi system) yields near-zero resonance energy.
    Expected: close to 0.
    """
    ethane_smiles = "CC"
    mol = Chem.MolFromSmiles(ethane_smiles)
    assert mol is not None, "Failed to parse ethane SMILES"

    resonance_energy = compute_huckel_resonance_energy(mol)

    # Ethane has no pi system, so resonance energy should be near zero
    assert np.isclose(resonance_energy, 0.0, atol=1.0), \
        f"Ethane resonance energy should be near zero, got {resonance_energy}"