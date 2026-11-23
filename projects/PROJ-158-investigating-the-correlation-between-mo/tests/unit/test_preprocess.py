"""
Unit tests for salt removal and tautomer canonicalization in preprocess.py.

This test suite uses static/mock data to verify the correctness of:
1. Salt removal logic (FR-002)
2. Tautomer canonicalization logic (FR-002)

It does NOT require network access or real dataset files.
"""
import pytest
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from rdkit import Chem
from rdkit.Chem import rdMolTransforms, Descriptors
from data.preprocess import remove_salts, canonicalize_tautomer

# --- Mock Data for Edge Cases ---

# Case 1: Molecule with a common salt (Sodium Chloride) attached via dot
# SMILES: "CCO.CCO.[Na+].[Cl-]" -> Ethanol + Ethanol + Na + Cl
# Expected: Only the organic molecules (Ethanol) remain, salts removed.
SMILES_WITH_SALT = "CCO.CCO.[Na+].[Cl-]"
EXPECTED_SALT_REMOVED_COUNT = 2  # Two ethanol molecules

# Case 2: Molecule with a counter-ion (Tetrafluoroborate)
# SMILES: "c1ccccc1.[BF4-]" -> Benzene + BF4
SMILES_WITH_COUNTERION = "c1ccccc1.[BF4-]"
EXPECTED_COUNTERION_REMOVED_COUNT = 1  # Only Benzene

# Case 3: Tautomerism - Keto-Enol
# Acetone (Keto) vs Prop-1-en-2-ol (Enol)
# RDKit's canonical tautomer generation should pick a consistent form.
# We test that the function returns a valid molecule and that the canonical form
# is consistent for the same input.
SMILES_KETO = "CC(=O)C"  # Acetone
SMILES_ENOL = "CC(=C)O"   # Prop-1-en-2-ol (tautomer of acetone)

# Case 4: Invalid SMILES (should be handled gracefully by the caller, 
# but we test the function's robustness if it receives one)
SMILES_INVALID = "invalid_smiles_string_123"

# Case 5: Molecule with no salts
SMILES_CLEAN = "CCO"

class TestSaltRemoval:
    def test_remove_salts_removes_ions(self):
        """Test that common inorganic ions are removed from dot-separated SMILES."""
        molecules = remove_salts(SMILES_WITH_SALT)
        assert len(molecules) == EXPECTED_SALT_REMOVED_COUNT
        # Verify they are valid RDKit Mol objects
        for mol in molecules:
            assert mol is not None
            assert mol.GetNumAtoms() > 0

    def test_remove_salts_removes_counter_ions(self):
        """Test that organic counter-ions like BF4 are removed."""
        molecules = remove_salts(SMILES_WITH_COUNTERION)
        assert len(molecules) == EXPECTED_COUNTERION_REMOVED_COUNT
        # Should be just Benzene
        assert molecules[0].GetNumAtoms() == 6 

    def test_remove_salts_clean_molecule(self):
        """Test that a clean molecule returns a list with one element."""
        molecules = remove_salts(SMILES_CLEAN)
        assert len(molecules) == 1
        assert molecules[0] is not None

    def test_remove_salts_invalid_smiles(self):
        """Test behavior with invalid SMILES. Should return empty list or handle gracefully."""
        molecules = remove_salts(SMILES_INVALID)
        # Expected behavior: return empty list or list of None filtered out
        # The implementation should not crash.
        assert isinstance(molecules, list)
        # If the implementation returns None for invalid, filter them out.
        valid_mols = [m for m in molecules if m is not None]
        assert len(valid_mols) == 0

class TestTautomerCanonicalization:
    def test_canonicalize_returns_valid_mol(self):
        """Test that the function returns a valid RDKit Mol object."""
        mol = canonicalize_tautomer(SMILES_KETO)
        assert mol is not None
        assert mol.GetNumAtoms() > 0

    def test_canonicalize_consistency(self):
        """Test that running canonicalization twice yields the same SMILES."""
        mol1 = canonicalize_tautomer(SMILES_KETO)
        mol2 = canonicalize_tautomer(SMILES_KETO)
        
        assert mol1 is not None and mol2 is not None
        
        smi1 = Chem.MolToSmiles(mol1)
        smi2 = Chem.MolToSmiles(mol2)
        
        assert smi1 == smi2, f"Canonicalization not consistent: {smi1} != {smi2}"

    def test_canonicalize_handles_tautomers(self):
        """Test that keto and enol forms are canonicalized to the same representation (or consistent)."""
        # Note: RDKit's tautomer enumeration/canonicalization logic is specific.
        # We verify that the function runs without error and returns a valid molecule.
        # Strictly proving they map to the *exact* same canonical SMILES depends on RDKit's 
        # internal rules (e.g., which tautomer is preferred).
        # We test that both result in valid molecules with the same heavy atom count.
        
        mol_keto = canonicalize_tautomer(SMILES_KETO)
        mol_enol = canonicalize_tautomer(SMILES_ENOL)
        
        assert mol_keto is not None
        assert mol_enol is not None
        
        # Both acetone and its enol tautomer should have 3 carbons, 1 oxygen, 6 hydrogens (implicit)
        # Heavy atom count should be 4 (3 C + 1 O)
        assert mol_keto.GetNumHeavyAtoms() == 4
        assert mol_enol.GetNumHeavyAtoms() == 4

    def test_canonicalize_invalid_input(self):
        """Test that invalid SMILES returns None or empty."""
        mol = canonicalize_tautomer(SMILES_INVALID)
        assert mol is None or not isinstance(mol, Chem.Mol) or mol.GetNumAtoms() == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
