"""
Unit tests for data ingestion logic, specifically focusing on RDKit SMILES parsing
and invalid row exclusion mechanisms.
"""
import pytest
import sys
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.ingest_utils import is_valid_smiles, parse_smiles_to_mol
from utils.logger import get_logger

logger = get_logger(__name__)


class TestSmilesParsing:
    """Tests for RDKit SMILES parsing and validation logic."""

    def test_valid_simple_smiles(self):
        """Test that valid simple SMILES (e.g., benzene) parse correctly."""
        smiles = "c1ccccc1"
        assert is_valid_smiles(smiles) is True
        mol = parse_smiles_to_mol(smiles)
        assert mol is not None
        assert mol.GetNumAtoms() == 6

    def test_valid_polymer_smiles(self):
        """Test that valid polymer-like SMILES parse correctly."""
        # Example: Polyethylene glycol fragment
        smiles = "CCOCCOCC"
        assert is_valid_smiles(smiles) is True
        mol = parse_smiles_to_mol(smiles)
        assert mol is not None

    def test_invalid_smiles_mismatched_parens(self):
        """Test that SMILES with mismatched parentheses are rejected."""
        smiles = "C(C"
        assert is_valid_smiles(smiles) is False
        mol = parse_smiles_to_mol(smiles)
        assert mol is None

    def test_invalid_smiles_mismatched_brackets(self):
        """Test that SMILES with mismatched brackets are rejected."""
        smiles = "C[C"
        assert is_valid_smiles(smiles) is False
        mol = parse_smiles_to_mol(smiles)
        assert mol is None

    def test_invalid_smiles_empty_string(self):
        """Test that empty SMILES strings are rejected."""
        smiles = ""
        assert is_valid_smiles(smiles) is False
        mol = parse_smiles_to_mol(smiles)
        assert mol is None

    def test_invalid_smiles_whitespace_only(self):
        """Test that whitespace-only SMILES strings are rejected."""
        smiles = "   "
        assert is_valid_smiles(smiles) is False
        mol = parse_smiles_to_mol(smiles)
        assert mol is None

    def test_invalid_smiles_garbage(self):
        """Test that random garbage strings are rejected."""
        smiles = "@#$%^&*"
        assert is_valid_smiles(smiles) is False
        mol = parse_smiles_to_mol(smiles)
        assert mol is None

    def test_invalid_smiles_undefined_atom(self):
        """Test that SMILES with undefined atoms are rejected."""
        # 'Z' is not a standard atom in RDKit without explicit isotopic/charge notation
        # RDKit usually parses 'Z' as an element but might fail sanitization if it's invalid context
        # Let's use a clearly invalid sequence
        smiles = "C(Z)C"
        # Depending on RDKit version, 'Z' might be parsed as an atom but fail sanitization
        # We rely on is_valid_smiles returning False if sanitization fails
        assert is_valid_smiles(smiles) is False

    def test_valid_smiles_with_stereochemistry(self):
        """Test that SMILES with stereochemistry are parsed correctly."""
        smiles = "C/C=C/C"  # trans-2-butene
        assert is_valid_smiles(smiles) is True
        mol = parse_smiles_to_mol(smiles)
        assert mol is not None

    def test_valid_smiles_with_rings(self):
        """Test that SMILES with ring closures are parsed correctly."""
        smiles = "C1CCCCC1"  # Cyclohexane
        assert is_valid_smiles(smiles) is True
        mol = parse_smiles_to_mol(smiles)
        assert mol is not None
        assert mol.GetNumAtoms() == 6

    def test_batch_validation_valid(self):
        """Test batch validation with all valid SMILES."""
        smiles_list = ["CC", "c1ccccc1", "C1CCCCC1"]
        results = [is_valid_smiles(s) for s in smiles_list]
        assert all(results)

    def test_batch_validation_mixed(self):
        """Test batch validation with mixed valid and invalid SMILES."""
        smiles_list = ["CC", "C(C", "c1ccccc1", "", "C1CCCCC1"]
        results = [is_valid_smiles(s) for s in smiles_list]
        # Expected: True, False, True, False, True
        expected = [True, False, True, False, True]
        assert results == expected

    def test_row_exclusion_logic_simulation(self):
        """
        Simulate the logic used in 01_ingest.py to exclude invalid rows.
        This verifies that the filtering mechanism correctly identifies bad rows.
        """
        mock_data = [
            {"smiles": "CC", "valid": True},
            {"smiles": "C(C", "valid": False},
            {"smiles": "c1ccccc1", "valid": True},
            {"smiles": "", "valid": False},
            {"smiles": "C1CCCCC1", "valid": True},
        ]

        valid_rows = []
        invalid_rows = []

        for row in mock_data:
            if is_valid_smiles(row["smiles"]):
                valid_rows.append(row)
            else:
                invalid_rows.append(row)

        assert len(valid_rows) == 3
        assert len(invalid_rows) == 2
        
        # Verify content of invalid rows
        invalid_smiles_values = [r["smiles"] for r in invalid_rows]
        assert "C(C" in invalid_smiles_values
        assert "" in invalid_smiles_values

class TestParseSmilesToMol:
    """Tests specifically for the parse_smiles_to_mol function."""

    def test_returns_rdkit_mol_object(self):
        """Ensure parse_smiles_to_mol returns an RDKit Mol object."""
        mol = parse_smiles_to_mol("CCO")
        assert mol is not None
        assert mol.GetNumAtoms() == 3

    def test_returns_none_for_invalid(self):
        """Ensure parse_smiles_to_mol returns None for invalid SMILES."""
        mol = parse_smiles_to_mol("INVALID")
        assert mol is None

    def test_handles_none_input(self):
        """Ensure parse_smiles_to_mol handles None input gracefully."""
        mol = parse_smiles_to_mol(None)
        assert mol is None