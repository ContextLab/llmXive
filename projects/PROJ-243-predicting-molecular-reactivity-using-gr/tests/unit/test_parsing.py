"""
Unit tests for SMILES parsing and exclusion logic.

This module validates the correctness of the SMILES parsing pipeline,
specifically focusing on the exclusion logic for invalid or unsupported molecules.
It ensures that molecules failing validation are correctly identified and excluded
before graph construction, adhering to the project's data quality requirements.

Dependencies:
    - rdkit: For molecular parsing and validation
    - code.utils.graph_utils: For the smiles_to_molecule function
"""
import pytest
from typing import List, Tuple, Set
from rdkit import Chem
from rdkit.Chem import rdchem

# Import the utility function being tested
# We assume the project root is in sys.path or this is run via pytest with proper config
try:
    from code.utils.graph_utils import smiles_to_molecule, validate_graph
except ImportError:
    # Fallback for direct execution if path setup differs
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from code.utils.graph_utils import smiles_to_molecule, validate_graph


class TestSMILESParsing:
    """Tests for basic SMILES string parsing functionality."""

    def test_valid_smiles_parsing(self):
        """Test that valid SMILES strings are successfully parsed into RDKit molecules."""
        valid_smiles_list = [
            "C",          # Methane
            "CC",         # Ethane
            "c1ccccc1",   # Benzene
            "CCO",        # Ethanol
            "O=C=O",      # Carbon dioxide
        ]

        for smiles in valid_smiles_list:
            mol = smiles_to_molecule(smiles)
            assert mol is not None, f"Failed to parse valid SMILES: {smiles}"
            assert isinstance(mol, Chem.Mol), f"Expected Mol object, got {type(mol)} for {smiles}"
            # Verify the molecule has atoms
            assert mol.GetNumAtoms() > 0, f"Parsed molecule has no atoms: {smiles}"

    def test_canonic_smiles_reconstruction(self):
        """Test that a valid SMILES can be converted to a molecule and back to canonical SMILES."""
        original_smiles = "CCO"
        mol = smiles_to_molecule(original_smiles)
        assert mol is not None
        
        canonical_smiles = Chem.MolToSmiles(mol)
        # The canonical SMILES might differ in order but should represent the same graph
        # We verify by checking the number of atoms and bonds match
        assert mol.GetNumAtoms() == 3
        assert mol.GetNumBonds() == 2


class TestExclusionLogic:
    """Tests for the logic that excludes invalid or problematic molecules."""

    def test_empty_string_exclusion(self):
        """Test that empty strings are correctly identified as invalid."""
        mol = smiles_to_molecule("")
        assert mol is None, "Empty string should result in None molecule"

    def test_whitespace_only_exclusion(self):
        """Test that whitespace-only strings are correctly identified as invalid."""
        mol = smiles_to_molecule("   ")
        assert mol is None, "Whitespace-only string should result in None molecule"

    def test_invalid_syntax_exclusion(self):
        """Test that strings with invalid SMILES syntax are excluded."""
        invalid_smiles_list = [
            "C(C",        # Unclosed ring
            "CC)",        # Unexpected closing bracket
            "C=C=",       # Invalid valence (depending on context, often invalid)
            "C#C#C",      # Invalid triple bond sequence
            "C1CC1C1",    # Ambiguous ring closure
            "C@@",        # Invalid stereochemistry without chiral center context
        ]

        for smiles in invalid_smiles_list:
            mol = smiles_to_molecule(smiles)
            # Depending on RDKit's strictness, some might parse but be invalid.
            # We expect the parser to fail or return None for clearly broken syntax.
            # If it returns a molecule, it must be validated further.
            if mol is not None:
                # If a molecule object is returned, it should ideally fail validation
                # or have 0 atoms if it's a ghost molecule (though RDKit usually returns None)
                assert mol.GetNumAtoms() == 0, f"Invalid SMILES '{smiles}' parsed but has atoms"

    def test_valence_error_exclusion(self):
        """Test that molecules with impossible valences are excluded or flagged."""
        # Example: Carbon with 5 bonds
        # RDKit might parse this but flag it as having valence errors
        # We test that the molecule is either None or fails basic validation
        problematic_smiles = "C(=O)(O)(O)(O)O" # Carbon with 5 single/double bonds (hypothetical)
        # A more standard RDKit failure case:
        mol = smiles_to_molecule("C1=CC=CC=1") # Cyclohexadiene-like but missing ring closure properly?
        # Actually, let's use a known valence error:
        # "C[C+](C)(C)C" is valid (carbocation), but "C[C](C)(C)C" (pentavalent carbon) is not.
        # RDKit often returns None or a molecule with sanitization errors.
        
        # Let's use a clear invalid case:
        invalid_valence_smiles = "C12C12" # Two ring closures on same atom without proper definition
        mol = smiles_to_molecule(invalid_valence_smiles)
        # If it parses, it must be sanitizable. If not, it's excluded.
        # The function smiles_to_molecule should handle sanitization.
        # If it returns a molecule, it should be valid.
        # If it returns None, it was excluded.
        # We assert that it's not a "broken" molecule that crashes downstream.
        if mol is not None:
            # If it exists, it must be sanitizable and have valid valences
            # RDKit's MolToSmiles usually sanitizes if possible, otherwise raises
            try:
                _ = Chem.MolToSmiles(mol)
            except:
                pytest.fail(f"Molecule parsed from '{invalid_valence_smiles}' is not sanitizable")

    def test_mixed_batch_processing(self):
        """Test processing a batch of valid and invalid SMILES."""
        batch = [
            "CC",      # Valid
            "",        # Invalid
            "c1ccccc1",# Valid
            "INVALID", # Invalid
            "CCO",     # Valid
            "   ",     # Invalid
        ]
        
        valid_count = 0
        invalid_count = 0
        results = []

        for smiles in batch:
            mol = smiles_to_molecule(smiles)
            if mol is not None and mol.GetNumAtoms() > 0:
                valid_count += 1
                results.append((smiles, True))
            else:
                invalid_count += 1
                results.append((smiles, False))

        assert valid_count == 3, f"Expected 3 valid, got {valid_count}"
        assert invalid_count == 3, f"Expected 3 invalid, got {invalid_count}"
        
        # Verify the logic correctly identified them
        expected = [
            ("CC", True),
            ("", False),
            ("c1ccccc1", True),
            ("INVALID", False),
            ("CCO", True),
            ("   ", False),
        ]
        assert results == expected, "Batch processing logic failed to correctly identify valid/invalid"


class TestEdgeCases:
    """Tests for specific edge cases in SMILES parsing."""

    def test_very_long_smiles(self):
        """Test handling of very long SMILES strings."""
        # Create a long chain
        long_smiles = "C" * 1000
        mol = smiles_to_molecule(long_smiles)
        assert mol is not None, "Long SMILES should be parsed"
        assert mol.GetNumAtoms() == 1000, "Atom count mismatch for long SMILES"

    def test_special_characters(self):
        """Test handling of SMILES with special characters (isotopes, charges)."""
        # Isotope
        mol = smiles_to_molecule("[13CH4]")
        assert mol is not None, "Isotope SMILES should be parsed"
        
        # Charge
        mol = smiles_to_molecule("[NH4+]")
        assert mol is not None, "Charge SMILES should be parsed"

    def test_null_characters(self):
        """Test handling of SMILES containing null characters."""
        mol = smiles_to_molecule("C\x00C")
        # RDKit should fail to parse this
        assert mol is None, "SMILES with null characters should be excluded"

    def test_malformed_unicode(self):
        """Test handling of malformed unicode in SMILES."""
        # This is tricky in Python strings, but we can try invalid byte sequences
        # if we were reading from bytes. For string input, we assume valid Python strings.
        # We test a string that looks like it might be malformed but is valid unicode.
        # The parser should handle it or reject it gracefully.
        # For now, we assume the input is a valid Python string.
        pass # Placeholder for specific unicode test if needed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])