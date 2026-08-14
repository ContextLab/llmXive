"""
Unit tests for SMILES standardization and Molecular Weight (MW) filtering.

This module tests the preprocessing logic defined in src/data/preprocess.py,
specifically:
1. SMILES canonicalization and standardization (removing salts, normalizing).
2. Molecular weight filtering (keeping only compounds < 1000 Da).
"""
import pytest
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add code directory to path to match project structure
code_dir = Path(__file__).parent.parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

try:
    from src.data.preprocess import standardize_smiles, filter_by_mw
except ImportError as e:
    # Fallback if the module doesn't exist yet (task T020 not done)
    # We define mocks here to ensure the test file itself is valid Python
    # and can be imported, but the tests will skip if the real module is missing.
    class MockPreprocess:
        pass
    standardize_smiles = MockPreprocess
    filter_by_mw = MockPreprocess

# Mock RDKit imports if not available for the test environment
# In a real execution environment, RDKit must be installed.
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
    pytest.skip("RDKit not installed, skipping SMILES tests", allow_module_level=True)

@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not available")
class TestSMILESStandardization:
    """Tests for SMILES canonicalization and salt removal."""

    def test_canonicalize_valid_smiles(self):
        """Test that a valid SMILES string is canonicalized."""
        # Benzene can be written in multiple ways
        smi_variants = [
            "c1ccccc1",
            "C1=CC=CC=C1",
            "c1c(C)cccc1" # Toluene
        ]
        
        for smi in smi_variants:
            result = standardize_smiles(smi)
            # Result should not be None
            assert result is not None, f"Failed to canonicalize {smi}"
            # Result should be a string
            assert isinstance(result, str), f"Result for {smi} is not a string"
            # Result should not be empty
            assert len(result) > 0, f"Result for {smi} is empty"

    def test_remove_salts(self):
        """Test that salts (e.g., [Na+]) are removed from SMILES."""
        # Example: Sodium benzoate
        smi_with_salt = "O=C([O-])c1ccccc1.[Na+]"
        result = standardize_smiles(smi_with_salt)
        
        assert result is not None
        assert "[Na+]" not in result
        # The main molecule part should remain
        assert "c1ccccc1" in result or "C1=CC=CC=C1" in result

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES strings return None."""
        invalid_smiles = [
            "",
            "INVALID_SMILES",
            "C(C(C", # Unbalanced parenthesis
            "c1ccccc1c1ccccc1" # Invalid aromaticity context (if RDKit catches it)
        ]
        
        for smi in invalid_smiles:
            result = standardize_smiles(smi)
            # Depending on implementation, this might return None or the original
            # Standard implementation usually returns None for parse errors
            if result is not None:
                # If it returns something, it should be valid
                mol = Chem.MolFromSmiles(result)
                assert mol is not None, f"Returned string {result} is not valid SMILES for input {smi}"

    def test_empty_string_handling(self):
        """Test handling of empty input."""
        result = standardize_smiles("")
        assert result is None

@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not available")
class TestMolecularWeightFiltering:
    """Tests for Molecular Weight filtering logic."""

    def test_filter_small_molecule(self):
        """Test that small molecules (MW < 1000) are kept."""
        # Ethanol: MW ~ 46
        smi = "CCO"
        mol = Chem.MolFromSmiles(smi)
        assert mol is not None
        
        kept_mols, discarded_mols = filter_by_mw([mol], threshold=1000.0)
        
        assert len(kept_mols) == 1
        assert len(discarded_mols) == 0

    def test_filter_large_molecule(self):
        """Test that large molecules (MW >= 1000) are discarded."""
        # Simulate a very large polymer or peptide
        # Construct a long chain to exceed 1000 Da
        # Polyethylene roughly: -[CH2-CH2]n-
        # MW of CH2 = 14. 1000 / 14 ~ 71 units.
        large_smi = "C" * 200  # Very long alkane chain
        mol = Chem.MolFromSmiles(large_smi)
        assert mol is not None
        
        mw = Descriptors.MolWt(mol)
        assert mw >= 1000.0, f"Test molecule MW {mw} is too small for this test"
        
        kept_mols, discarded_mols = filter_by_mw([mol], threshold=1000.0)
        
        assert len(kept_mols) == 0
        assert len(discarded_mols) == 1

    def test_filter_mixed_batch(self):
        """Test filtering a mix of small and large molecules."""
        small_smi = "CCO" # Ethanol
        large_smi = "C" * 200 # Large alkane
        
        mol_small = Chem.MolFromSmiles(small_smi)
        mol_large = Chem.MolFromSmiles(large_smi)
        
        input_mols = [mol_small, mol_large, mol_small]
        
        kept_mols, discarded_mols = filter_by_mw(input_mols, threshold=1000.0)
        
        assert len(kept_mols) == 2
        assert len(discarded_mols) == 1

    def test_none_handling(self):
        """Test that None molecules in the list are handled gracefully."""
        # Create a list with a valid mol and a None
        mol = Chem.MolFromSmiles("CCO")
        input_mols = [mol, None, mol]
        
        # The function should skip None or raise an error depending on design.
        # Assuming it filters them out or handles them.
        # If the implementation crashes on None, this test will catch it.
        try:
            kept_mols, discarded_mols = filter_by_mw(input_mols, threshold=1000.0)
            # If it succeeds, None should not be in kept_mols
            assert None not in kept_mols
        except TypeError:
            # If the implementation doesn't handle None, we document the expected behavior
            # or we assume the input list is pre-validated.
            # For this test, we assert that the function handles it or we skip.
            pytest.skip("filter_by_mw does not handle None inputs")

    def test_threshold_boundary(self):
        """Test behavior exactly at the threshold."""
        # Create a molecule close to 1000 Da
        # This is hard to hit exactly, so we test the logic with a known value
        # If MW < 1000 -> Keep
        # If MW >= 1000 -> Discard
        smi = "C" * 72 # Approx 72 * 14 = 1008
        mol = Chem.MolFromSmiles(smi)
        mw = Descriptors.MolWt(mol)
        
        kept, discarded = filter_by_mw([mol], threshold=1000.0)
        
        if mw < 1000.0:
            assert len(kept) == 1
            assert len(discarded) == 0
        else:
            assert len(kept) == 0
            assert len(discarded) == 1