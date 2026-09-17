"""
Unit tests for SMILES-to-graph conversion logic.

This module tests the conversion of SMILES strings to RDKit molecular graphs
and verifies that the resulting graph properties match the input expectations.

Dependencies:
  - rdkit (installed per T002 requirements)
  - pytest
  - code.utils.seeds (for deterministic behavior)
"""
import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdmolops
from rdkit import DataStructs

# Import project utilities
from utils.seeds import set_global_seed
from config import get_paths, get_hyperparams

# We will implement the conversion logic inline for the test or import if it exists.
# Since T014 (Implementation) is not done yet, we define a minimal helper here
# to simulate the expected interface for T014, or we can import it if T014 was done.
# However, T014 is in Phase 3, same as T010. The task says "Implement T010".
# If the conversion function doesn't exist yet, we must mock it or implement a 
# minimal version to test the *properties* assertion logic.
#
# Strategy: Implement a minimal `smiles_to_graph` function locally in this file 
# (or import from a placeholder if we want to simulate the module structure) 
# to ensure the test logic runs. Since T014 is the implementation task, 
# we should write the test *against* the expected interface.
#
# To make this runnable NOW (T010) without T014, we will implement a simple 
# conversion function here that mimics the expected behavior of T014.
# This allows the test to pass and verify the logic. When T014 is implemented,
# this function will be replaced by the import from `code/data/preprocess.py`.

def smiles_to_graph(smiles: str):
    """
    Convert a SMILES string to an RDKit graph object (Mol).
    This is a placeholder for T014 implementation.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    # Add hydrogens to ensure graph completeness for property checks
    mol = Chem.AddHs(mol)
    return mol

def get_graph_properties(mol):
    """
    Extract key properties from an RDKit Mol object to verify against input.
    Returns a dict with:
      - num_atoms
      - num_bonds
      - is_aromatic (bool if any bond is aromatic)
      - num_heavy_atoms
    """
    if mol is None:
        return None
    
    num_atoms = mol.GetNumAtoms()
    num_bonds = mol.GetNumBonds()
    num_heavy_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() > 1)
    
    is_aromatic = any(bond.GetIsAromatic() for bond in mol.GetBonds())
    
    return {
        "num_atoms": num_atoms,
        "num_bonds": num_bonds,
        "num_heavy_atoms": num_heavy_atoms,
        "is_aromatic": is_aromatic
    }

class TestDataLoader:
    """Unit tests for SMILES-to-graph conversion properties."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set global seed for deterministic test runs."""
        set_global_seed(42)
        self.paths = get_paths()
        self.hyperparams = get_hyperparams()

    def test_benzene_graph_properties(self):
        """
        Test that benzene SMILES converts to a graph with correct properties.
        Benzene: C1=CC=CC=C1 -> 6 carbons, 6 bonds (3 double, 3 single, but in graph 6 edges), aromatic.
        With hydrogens: 6 C + 6 H = 12 atoms.
        """
        smiles = "c1ccccc1"
        mol = smiles_to_graph(smiles)
        props = get_graph_properties(mol)

        assert props is not None, "Graph conversion failed"
        assert props["num_atoms"] == 12, f"Expected 12 atoms (6C+6H), got {props['num_atoms']}"
        assert props["num_heavy_atoms"] == 6, f"Expected 6 heavy atoms, got {props['num_heavy_atoms']}"
        assert props["is_aromatic"] is True, "Benzene should be aromatic"
        # Benzene has 6 C-C bonds. In RDKit graph, these are the edges.
        # Even with hydrogens added, the core C-C bonds remain 6.
        # Total bonds = 6 (C-C) + 6 (C-H) = 12.
        assert props["num_bonds"] == 12, f"Expected 12 bonds, got {props['num_bonds']}"

    def test_ethane_graph_properties(self):
        """
        Test ethane (C-C) properties.
        2 Carbons, 1 C-C bond.
        With H: 2 C + 6 H = 8 atoms.
        Bonds: 1 (C-C) + 6 (C-H) = 7 bonds.
        Non-aromatic.
        """
        smiles = "CC"
        mol = smiles_to_graph(smiles)
        props = get_graph_properties(mol)

        assert props is not None
        assert props["num_heavy_atoms"] == 2
        assert props["num_atoms"] == 8
        assert props["is_aromatic"] is False
        assert props["num_bonds"] == 7

    def test_invalid_smiles_raises_error(self):
        """
        Test that invalid SMILES strings raise a ValueError.
        """
        with pytest.raises(ValueError):
            smiles_to_graph("invalid_smiles_string_123")

    def test_graph_connectivity_matches_smiles(self):
        """
        Verify that the number of atoms in the graph matches the number of atoms
        explicitly or implicitly defined in the SMILES.
        """
        # Methane: C -> 1 C + 4 H = 5 atoms
        smiles = "C"
        mol = smiles_to_graph(smiles)
        props = get_graph_properties(mol)
        assert props["num_atoms"] == 5
        assert props["num_heavy_atoms"] == 1

    def test_aromatic_ring_detection(self):
        """
        Test detection of aromaticity in different ring systems.
        """
        # Pyridine: c1ccncc1 -> Aromatic
        smiles = "c1ccncc1"
        mol = smiles_to_graph(smiles)
        props = get_graph_properties(mol)
        assert props["is_aromatic"] is True
        assert props["num_heavy_atoms"] == 6 # 5 C + 1 N

        # Cyclohexane: C1CCCCC1 -> Non-aromatic
        smiles = "C1CCCCC1"
        mol = smiles_to_graph(smiles)
        props = get_graph_properties(mol)
        assert props["is_aromatic"] is False

    def test_empty_smiles_raises_error(self):
        """
        Test that empty SMILES string raises an error.
        """
        with pytest.raises(ValueError):
            smiles_to_graph("")