"""
Unit tests for SHAP bit-to-substructure mapping functionality.

This module validates the logic for mapping fingerprint bits to chemical
substructures using RDKit, ensuring the explainability pipeline correctly
identifies structural contexts for model predictions.

Tests verify:
1. Correct bit extraction from fingerprint objects.
2. Proper substructure matching against RDKit patterns.
3. Handling of unmapped bits (bits with no corresponding substructure).
4. Integration with the expected output schema for deviation contexts.
"""

import pytest
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.explainability import map_bits_to_substructures, get_bit_info


class TestBitToSubstructureMapping:
    """Unit tests for the SHAP bit-to-substructure mapping logic."""

    @pytest.fixture
    def sample_molecules(self):
        """Create a list of sample RDKit molecule objects."""
        smiles_list = [
            "CCO",  # Ethanol
            "CC(=O)O",  # Acetic acid
            "c1ccccc1",  # Benzene
            "CC(C)C",  # Isobutane
            "CCN(CC)CC",  # Triethylamine
        ]
        mols = [Chem.MolFromSmiles(s) for s in smiles_list]
        return mols

    @pytest.fixture
    def sample_fingerprints(self, sample_molecules):
        """Generate ECFP4 fingerprints for sample molecules."""
        fps = []
        for mol in sample_molecules:
            if mol is not None:
                fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
                fps.append(fp)
        return fps

    def test_bit_extraction(self, sample_fingerprints):
        """Test that bits can be correctly extracted from fingerprint objects."""
        # Convert fingerprints to numpy arrays for bit checking
        for fp in sample_fingerprints:
            arr = np.zeros((2048,), dtype=int)
            fp.ConvertToNumpyArray(arr)
            # Verify array shape matches expected bit length
            assert arr.shape == (2048,)
            # Verify values are binary (0 or 1)
            assert set(arr).issubset({0, 1})

    def test_substructure_mapping_basic(self, sample_molecules):
        """Test basic mapping of bits to substructures using RDKit."""
        # Create a simple fingerprint and map bits
        if sample_molecules[0] is None:
            pytest.skip("Molecule creation failed")

        fp = AllChem.GetMorganFingerprintAsMol(
            sample_molecules[0], 2, useChirality=False
        )
        # Get bit info for the fingerprint
        bit_info = {}
        AllChem.GetBitInfo(fp, bit_info)

        # Verify bit info is a dictionary
        assert isinstance(bit_info, dict)
        # Verify keys are integers (bit indices)
        for bit_idx in bit_info:
            assert isinstance(bit_idx, int)

    def test_mapping_empty_fingerprint(self):
        """Test mapping behavior with an empty or invalid fingerprint."""
        empty_mol = Chem.MolFromSmiles("")
        assert empty_mol is None

        # Test with a valid but small molecule that might have few bits
        small_mol = Chem.MolFromSmiles("C")
        if small_mol:
            fp = AllChem.GetMorganFingerprintAsBitVect(small_mol, 2, nBits=2048)
            # Should not raise an error even if few bits are set
            result = map_bits_to_substructures([fp], [small_mol])
            assert isinstance(result, pd.DataFrame)

    def test_mapping_output_schema(self, sample_molecules, sample_fingerprints):
        """Test that the mapping output conforms to the expected schema."""
        if not sample_molecules or not sample_fingerprints:
            pytest.skip("Sample data unavailable")

        result_df = map_bits_to_substructures(sample_fingerprints, sample_molecules)

        # Verify output is a DataFrame
        assert isinstance(result_df, pd.DataFrame)

        # Verify expected columns exist
        expected_columns = [
            "bit_index",
            "substructure_smiles",
            "atom_indices",
            "molecule_smiles",
            "frequency",
        ]
        for col in expected_columns:
            assert col in result_df.columns, f"Missing expected column: {col}"

        # Verify data types
        assert result_df["bit_index"].dtype in [np.int64, np.int32]
        assert result_df["frequency"].dtype in [np.int64, np.int32]

    def test_mapping_with_known_substructures(self):
        """Test mapping with molecules containing known substructures."""
        # Molecule with a clear benzene ring
        benzene_smiles = "c1ccccc1"
        benzene_mol = Chem.MolFromSmiles(benzene_smiles)

        if benzene_mol is None:
            pytest.skip("Failed to create benzene molecule")

        fp = AllChem.GetMorganFingerprintAsBitVect(benzene_mol, 2, nBits=2048)
        result_df = map_bits_to_substructures([fp], [benzene_mol])

        # Should have at least one entry
        assert len(result_df) > 0

        # Check that substructure SMILES are valid
        for _, row in result_df.iterrows():
            sub_smiles = row["substructure_smiles"]
            if pd.notna(sub_smiles) and sub_smiles != "":
                # Verify the substructure can be parsed
                sub_mol = Chem.MolFromSmiles(sub_smiles)
                assert sub_mol is not None, f"Invalid substructure SMILES: {sub_smiles}"

    def test_unmapped_bits_handling(self, sample_molecules):
        """Test that unmapped bits are handled gracefully."""
        # Create a molecule that might have bits without clear substructures
        complex_mol = Chem.MolFromSmiles(
            "CC(C)(C)C(=O)Nc1ccc(cc1)S(=O)(=O)N"
        )  # Complex sulfonamide

        if complex_mol is None:
            pytest.skip("Failed to create complex molecule")

        fp = AllChem.GetMorganFingerprintAsBitVect(complex_mol, 2, nBits=2048)
        result_df = map_bits_to_substructures([fp], [complex_mol])

        # Should not fail even if some bits have no clear substructure mapping
        assert isinstance(result_df, pd.DataFrame)

    def test_frequency_calculation(self, sample_molecules):
        """Test that frequency counts are calculated correctly across molecules."""
        # Create multiple molecules with overlapping substructures
        overlapping_smiles = [
            "CCO",  # Ethanol
            "CCCO",  # Propanol
            "CCCCO",  # Butanol
        ]
        mols = [Chem.MolFromSmiles(s) for s in overlapping_smiles]
        fps = [
            AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
            for m in mols
            if m is not None
        ]

        if not fps:
            pytest.skip("Failed to create fingerprints")

        result_df = map_bits_to_substructures(fps, mols)

        # Verify frequency column exists and has valid values
        assert "frequency" in result_df.columns
        assert all(result_df["frequency"] >= 1)

    def test_integration_with_deviation_contexts(self, sample_molecules):
        """Test that mapping output can be used for deviation context analysis."""
        if not sample_molecules:
            pytest.skip("Sample data unavailable")

        # Filter valid molecules
        valid_mols = [m for m in sample_molecules if m is not None]
        if not valid_mols:
            pytest.skip("No valid molecules")

        fps = [
            AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
            for m in valid_mols
        ]

        result_df = map_bits_to_substructures(fps, valid_mols)

        # Verify the result can be saved to CSV (simulating deviation_contexts.csv)
        try:
            # Check if all required columns for CSV export are present
            required_for_csv = [
                "bit_index",
                "substructure_smiles",
                "molecule_smiles",
            ]
            assert all(col in result_df.columns for col in required_for_csv)
        except Exception as e:
            pytest.fail(f"Result DataFrame cannot be used for CSV export: {e}")

    def test_bit_info_extraction(self, sample_molecules):
        """Test the get_bit_info helper function."""
        if not sample_molecules or sample_molecules[0] is None:
            pytest.skip("Sample data unavailable")

        mol = sample_molecules[0]
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)

        bit_info = get_bit_info(fp)

        # Verify return type
        assert isinstance(bit_info, dict)

        # Verify structure if bits are set
        arr = np.zeros((2048,), dtype=int)
        fp.ConvertToNumpyArray(arr)
        set_bits = np.where(arr == 1)[0]

        if len(set_bits) > 0:
            for bit_idx in set_bits:
                assert bit_idx in bit_info
                assert isinstance(bit_info[bit_idx], list)
                for atom_tuple in bit_info[bit_idx]:
                    assert isinstance(atom_tuple, tuple)
                    assert len(atom_tuple) == 2  # (atom_index, radius)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])