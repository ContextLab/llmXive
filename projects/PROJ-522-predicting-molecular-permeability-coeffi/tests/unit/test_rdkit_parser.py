"""
Unit tests for RDKit parsing and duplicate handling logic.

This module validates:
1. SMILES to Mol conversion (valid and invalid inputs).
2. Descriptor computation for valid molecules.
3. Duplicate handling logic (aggregation of targets).
"""
import pytest
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

# Import the specific functions we are testing from the ingestion module
# The ingestion module is expected to expose these based on the API surface provided.
# We import them directly to test their logic in isolation.
from ingestion import parse_smiles_to_mol, compute_descriptors, handle_duplicates


class TestParseSmilesToMol:
    """Tests for the parse_smiles_to_mol function."""

    def test_valid_smiles_returns_mol_object(self):
        """Valid SMILES should return an RDKit Mol object."""
        smiles = "CCO"  # Ethanol
        mol = parse_smiles_to_mol(smiles)
        assert mol is not None
        assert isinstance(mol, Chem.Mol)
        assert mol.GetNumAtoms() == 3

    def test_valid_complex_smiles(self):
        """Test with a more complex valid SMILES."""
        smiles = "c1ccccc1"  # Benzene
        mol = parse_smiles_to_mol(smiles)
        assert mol is not None
        assert mol.GetNumAtoms() == 6

    def test_invalid_smiles_returns_none(self):
        """Invalid SMILES should return None."""
        invalid_smiles = "invalid_smiles_string_123"
        mol = parse_smiles_to_mol(invalid_smiles)
        assert mol is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        mol = parse_smiles_to_mol("")
        assert mol is None

    def test_none_input_returns_none(self):
        """None input should return None."""
        mol = parse_smiles_to_mol(None)
        assert mol is None


class TestComputeDescriptors:
    """Tests for the compute_descriptors function."""

    def test_compute_descriptors_returns_dict(self):
        """compute_descriptors should return a dictionary of descriptors."""
        smiles = "CCO"
        descriptors = compute_descriptors(smiles)
        assert isinstance(descriptors, dict)
        # Check for expected standard descriptors
        assert "MolWt" in descriptors
        assert "LogP" in descriptors
        assert "NumHDonors" in descriptors

    def test_compute_descriptors_values_are_numbers(self):
        """Descriptor values should be numeric."""
        smiles = "CCO"
        descriptors = compute_descriptors(smiles)
        for key, value in descriptors.items():
            assert isinstance(value, (int, float, np.floating, np.integer))

    def test_compute_descriptors_invalid_smiles_returns_empty_dict(self):
        """Invalid SMILES should result in an empty dict or None handling."""
        # Assuming the function handles invalid input gracefully
        descriptors = compute_descriptors("invalid")
        # Based on typical implementation, it might return empty or raise.
        # We assume it returns empty dict for invalid input to allow pipeline to continue/fail gracefully later.
        assert descriptors == {}


class TestHandleDuplicates:
    """Tests for the handle_duplicates function."""

    def test_no_duplicates_returns_original(self):
        """If no duplicates exist, the dataframe should remain effectively the same."""
        data = {
            "smiles": ["CCO", "CC", "c1ccccc1"],
            "target": [0.5, 0.6, 0.7],
            "source_id": ["A", "B", "C"]
        }
        df = pd.DataFrame(data)
        result = handle_duplicates(df)
        
        # Should have 3 rows
        assert len(result) == 3
        # Check that unique SMILES are preserved
        assert len(result["smiles"].unique()) == 3

    def test_duplicates_aggregated_with_mean(self):
        """Duplicates should be aggregated using the mean of the target."""
        data = {
            "smiles": ["CCO", "CCO", "CC"],
            "target": [0.4, 0.6, 0.5],
            "source_id": ["A", "B", "C"]
        }
        df = pd.DataFrame(data)
        result = handle_duplicates(df)

        # Should have 2 rows (CCO and CC)
        assert len(result) == 2

        # Find the CCO row
        cco_row = result[result["smiles"] == "CCO"].iloc[0]
        
        # The target should be the mean of 0.4 and 0.6 -> 0.5
        assert np.isclose(cco_row["target_mean"], 0.5)
        
        # The count should be 2
        assert cco_row["count"] == 2

    def test_duplicate_output_schema(self):
        """The output dataframe must have the correct columns."""
        data = {
            "smiles": ["CCO", "CCO"],
            "target": [0.5, 0.5],
            "source_id": ["A", "B"]
        }
        df = pd.DataFrame(data)
        result = handle_duplicates(df)

        expected_columns = ["smiles", "target_mean", "count", "source_id"]
        assert list(result.columns) == expected_columns

    def test_source_id_aggregation(self):
        """The source_id column should list all source IDs for the duplicate."""
        data = {
            "smiles": ["CCO", "CCO", "CCO"],
            "target": [0.5, 0.5, 0.5],
            "source_id": ["NIST", "PubChem", "MTR"]
        }
        df = pd.DataFrame(data)
        result = handle_duplicates(df)

        cco_row = result[result["smiles"] == "CCO"].iloc[0]
        # The source_id should contain all three sources
        assert "NIST" in str(cco_row["source_id"])
        assert "PubChem" in str(cco_row["source_id"])
        assert "MTR" in str(cco_row["source_id"])
        assert cco_row["count"] == 3