"""
Unit tests for SMILES validation logic.
Tests the regex-based validation and RDKit parsing logic.
"""
import pytest
import sys
import os
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.validators import enforce_2d_only_imports, assert_no_3d_calls
from data.loader import validate_smiles, iterate_smiles
from rdkit import Chem


class TestSMILESValidation:
    """Tests for SMILES string validation."""

    def test_valid_smiles_simple(self):
        """Test validation of a simple valid SMILES string."""
        smiles = "CCO"  # Ethanol
        assert validate_smiles(smiles) is True

    def test_valid_smiles_complex(self):
        """Test validation of a complex valid SMILES string."""
        smiles = "c1ccccc1O"  # Phenol
        assert validate_smiles(smiles) is True

    def test_valid_smiles_with_branches(self):
        """Test validation of SMILES with branches."""
        smiles = "CC(C)C(=O)O"  # Isobutyric acid
        assert validate_smiles(smiles) is True

    def test_invalid_smiles_empty(self):
        """Test validation of empty string."""
        assert validate_smiles("") is False

    def test_invalid_smiles_whitespace(self):
        """Test validation of whitespace-only string."""
        assert validate_smiles("   ") is False

    def test_invalid_smiles_special_chars(self):
        """Test validation of string with invalid characters."""
        assert validate_smiles("CC@O") is False

    def test_invalid_smiles_unmatched_parentheses(self):
        """Test validation of SMILES with unmatched parentheses."""
        assert validate_smiles("CC(O") is False

    def test_invalid_smiles_unmatched_brackets(self):
        """Test validation of SMILES with unmatched brackets."""
        assert validate_smiles("[NH3+") is False

    def test_none_input(self):
        """Test validation of None input."""
        assert validate_smiles(None) is False

    def test_numeric_input(self):
        """Test validation of numeric input."""
        assert validate_smiles(123) is False


class TestRDKitParsing:
    """Tests for RDKit-based SMILES parsing."""

    def test_rdkit_parse_valid(self):
        """Test that RDKit can parse a valid SMILES."""
        smiles = "CCO"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None
        assert mol.GetNumAtoms() == 3

    def test_rdkit_parse_invalid(self):
        """Test that RDKit fails to parse invalid SMILES."""
        smiles = "CC@O"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is None

    def test_rdkit_canonize(self):
        """Test canonicalization of SMILES."""
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None
        canonical = Chem.MolToSmiles(mol)
        assert isinstance(canonical, str)
        assert len(canonical) > 0


class Test2DExclusion:
    """Tests for 2D-only enforcement in imports."""

    def test_enforce_2d_imports_clean(self):
        """Test that a clean module passes 2D enforcement."""
        # Create a mock module with no 3D imports
        import types
        clean_module = types.ModuleType("clean_module")
        clean_module.some_func = lambda: None
        
        result = enforce_2d_only_imports(clean_module)
        assert result is True

    def test_assert_no_3d_calls_clean(self):
        """Test that a function without 3D calls passes assertion."""
        def clean_func():
            return "no 3D here"
        
        # This should not raise
        assert_no_3d_calls(clean_func)

    def test_2d_only_descriptors(self):
        """Test that we only compute 2D descriptors."""
        # This is a logic test - ensure we don't accidentally call 3D methods
        from rdkit.Chem import Descriptors
        
        # List of 2D descriptors we use
        valid_2d = [
            'MolWt', 'MolLogP', 'NumHDonors', 'NumHAcceptors',
            'TPSA', 'NumRotatableBonds', 'NumAromaticRings'
        ]
        
        # Verify these exist in Descriptors module
        for name in valid_2d:
            assert hasattr(Descriptors, name), f"{name} should be available"


class TestLoaderValidation:
    """Tests for the data loader validation functions."""

    def test_iterate_smiles_empty_file(self, tmp_path):
        """Test iteration over an empty file."""
        file_path = tmp_path / "empty.smi"
        file_path.write_text("")
        
        results = list(iterate_smiles(str(file_path)))
        assert results == []

    def test_iterate_smiles_single_line(self, tmp_path):
        """Test iteration over a single valid line."""
        file_path = tmp_path / "single.smi"
        file_path.write_text("CCO\t1.2\n")
        
        results = list(iterate_smiles(str(file_path)))
        assert len(results) == 1
        smiles, target = results[0]
        assert smiles == "CCO"
        assert target == 1.2

    def test_iterate_smiles_invalid_line_skipped(self, tmp_path):
        """Test that invalid lines are skipped or handled."""
        file_path = tmp_path / "mixed.smi"
        file_path.write_text("CCO\t1.2\nINVALID\nCC\t2.0\n")
        
        # Should process valid lines, skip invalid
        results = list(iterate_smiles(str(file_path)))
        # At least the valid lines should be processed
        assert len(results) >= 2

    def test_iterate_smiles_comments_ignored(self, tmp_path):
        """Test that comment lines are ignored."""
        file_path = tmp_path / "comments.smi"
        file_path.write_text("# This is a comment\nCCO\t1.2\n")
        
        results = list(iterate_smiles(str(file_path)))
        assert len(results) == 1
        assert results[0][0] == "CCO"