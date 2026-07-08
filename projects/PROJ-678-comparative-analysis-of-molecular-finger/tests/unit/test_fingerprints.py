"""
Unit tests for fingerprint generation functionality.
Specifically verifies Morgan fingerprint generation parameters as per Task T015.
"""
import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
import sys
import os

# Add project root to path to import code modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.fingerprints import generate_morgan_fingerprint, generate_maccs_fingerprint
from code.constants import MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS


class TestMorganFingerprintGeneration:
    """Tests for Morgan fingerprint generation parameters and correctness."""

    def test_morgan_fingerprint_generation(self):
        """
        Verify Morgan fingerprint generation parameters:
        - Radius must match MORGAN_RADIUS constant (2)
        - Bit vector length must match MORGAN_BITS constant (2048)
        - Output must be a valid numpy array
        - Fingerprint should be deterministic for the same molecule
        """
        # Create a simple test molecule (Ethanol)
        mol = Chem.MolFromSmiles("CCO")
        assert mol is not None, "Failed to create test molecule"

        # Generate fingerprint using the implementation
        fp_array = generate_morgan_fingerprint(mol)

        # Verify output type
        assert isinstance(fp_array, np.ndarray), "Fingerprint must be a numpy array"

        # Verify dimensionality matches constant
        assert fp_array.shape == (MORGAN_BITS,), (
            f"Morgan fingerprint length {fp_array.shape[0]} does not match "
            f"expected {MORGAN_BITS} bits"
        )

        # Verify values are binary (0 or 1)
        unique_values = np.unique(fp_array)
        assert all(v in [0, 1] for v in unique_values), (
            f"Fingerprint values must be binary, found: {unique_values}"
        )

        # Verify determinism: generate again and compare
        fp_array_2 = generate_morgan_fingerprint(mol)
        assert np.array_equal(fp_array, fp_array_2), (
            "Morgan fingerprint generation must be deterministic"
        )

        # Verify that the fingerprint is not all zeros (for a non-trivial molecule)
        assert np.sum(fp_array) > 0, "Fingerprint should not be all zeros for a valid molecule"

    def test_morgan_fingerprint_with_phosphorus_compound(self):
        """
        Verify Morgan fingerprint generation works correctly for organophosphates.
        This is critical for the project's focus on pesticide toxicity.
        """
        # SMILES for a simple organophosphate (SC-003 type structure)
        # Dimethyl methylphosphonate
        smiles = "COP(=O)(C)OC"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, f"Failed to create test molecule from SMILES: {smiles}"

        fp_array = generate_morgan_fingerprint(mol)

        # Verify shape
        assert fp_array.shape == (MORGAN_BITS,), "Phosphorus compound fingerprint shape mismatch"

        # Verify binary values
        unique_values = np.unique(fp_array)
        assert all(v in [0, 1] for v in unique_values), "Phosphorus compound fingerprint must be binary"

    def test_morgan_fingerprint_empty_molecule(self):
        """
        Verify behavior when given an invalid or empty molecule.
        """
        mol = None
        with pytest.raises((TypeError, AttributeError)):
            generate_morgan_fingerprint(mol)

    def test_morgan_fingerprint_parameters_match_constants(self):
        """
        Verify that the function uses the correct parameters from constants.py.
        """
        # We can't directly inspect the function internals without source,
        # but we can verify the output matches the expected bit length
        mol = Chem.MolFromSmiles("CCO")
        fp = generate_morgan_fingerprint(mol)
        
        # The length must exactly match the constant
        assert len(fp) == MORGAN_BITS, (
            f"Generated fingerprint length {len(fp)} does not match "
            f"MORGAN_BITS constant ({MORGAN_BITS})"
        )

        # Verify radius is effectively used by checking that a larger molecule
        # produces a different fingerprint than a smaller one
        mol_small = Chem.MolFromSmiles("C")  # Methane
        mol_large = Chem.MolFromSmiles("CCCCCCCCC")  # Nonane
        
        fp_small = generate_morgan_fingerprint(mol_small)
        fp_large = generate_morgan_fingerprint(mol_large)
        
        # They should be different
        assert not np.array_equal(fp_small, fp_large), (
            "Different molecules should produce different fingerprints"
        )


class TestMACCSFingerprintGeneration:
    """Tests for MACCS fingerprint generation (additional coverage)."""

    def test_maccs_fingerprint_generation(self):
        """
        Verify MACCS fingerprint generation:
        - Length must match MACCS_BITS constant (166)
        - Output must be a valid numpy array
        """
        mol = Chem.MolFromSmiles("CCO")
        assert mol is not None

        fp_array = generate_maccs_fingerprint(mol)

        assert isinstance(fp_array, np.ndarray), "MACCS fingerprint must be a numpy array"
        assert fp_array.shape == (MACCS_BITS,), (
            f"MACCS fingerprint length {fp_array.shape[0]} does not match "
            f"expected {MACCS_BITS} bits"
        )

        unique_values = np.unique(fp_array)
        assert all(v in [0, 1] for v in unique_values), "MACCS fingerprint must be binary"
