"""
Unit tests for the SMARTS-based filtering logic (T012).
"""
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import os

# Import the function to test
# Ensure the import path matches the project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from filter import apply_smarts_filter, load_compounds
from constants import SMARTS_PATTERN

class TestSmartsFilter:
    """Tests for the SMARTS filtering logic."""

    def test_smarts_filter_returns_empty_on_no_match(self):
        """
        Verify that the filter returns an empty list (DataFrame) when 
        no compounds match the SMARTS pattern.
        """
        # Create a mock DataFrame with SMILES that definitely do NOT match 
        # the organophosphate pattern [P](=O)([O,SC])[O,SC]
        # Example: Ethanol (no phosphorus)
        data = {
            'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
            'NR-AR': [0.5, 0.6, 0.7]
        }
        df = pd.DataFrame(data)

        result = apply_smarts_filter(df, SMARTS_PATTERN)

        assert result.empty, "Expected empty DataFrame when no compounds match SMARTS"
        assert len(result) == 0

    def test_smarts_filter_returns_matches(self):
        """
        Verify that the filter correctly identifies compounds matching the SMARTS pattern.
        """
        # Create a mock DataFrame with:
        # 1. A compound that matches (Organophosphate-like structure)
        # 2. A compound that does not match
        # Note: We need a valid SMILES for an organophosphate. 
        # Example: Parathion (simplified) or a generic OP structure.
        # A simple phosphorus-containing SMILES: 'OP(=O)(OC)OC' (Trimethyl phosphate)
        # This matches [P](=O)([O,SC])[O,SC] (P double bonded to O, and single bonded to O/S/C)
        
        data = {
            'smiles': [
                'OP(=O)(OC)OC',  # Matches (Organophosphate)
                'CCO',           # Does not match
                'OP(=O)(O)O'     # Matches (Phosphoric acid, though usually OPs have esters, the pattern allows O)
            ],
            'NR-AR': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)

        result = apply_smarts_filter(df, SMARTS_PATTERN)

        assert not result.empty, "Expected matches for organophosphate structures"
        assert len(result) >= 1, "Should have found at least one match"
        
        # Verify the returned SMILES are the correct ones
        result_smiles = set(result['smiles'].tolist())
        assert 'OP(=O)(OC)OC' in result_smiles, "Trimethyl phosphate should be included"
        assert 'CCO' not in result_smiles, "Ethanol should be excluded"

    def test_invalid_smiles_handling(self):
        """
        Verify that invalid SMILES strings are handled gracefully (skipped).
        """
        data = {
            'smiles': [
                'INVALID_SMILES_STRING',
                'CCO',
                None,
                ''
            ],
            'NR-AR': [0.1, 0.2, 0.3, 0.4]
        }
        df = pd.DataFrame(data)

        # Should not raise an exception
        result = apply_smarts_filter(df, SMARTS_PATTERN)
        
        # None of these should match the OP pattern anyway, so result should be empty
        assert result.empty

    def test_invalid_smarts_pattern(self):
        """
        Verify that an invalid SMARTS pattern raises an error.
        """
        data = {'smiles': ['CCO'], 'NR-AR': [0.1]}
        df = pd.DataFrame(data)

        with pytest.raises(ValueError) as exc_info:
            apply_smarts_filter(df, "INVALID_SMARTS[")
        
        assert "Invalid SMARTS pattern" in str(exc_info.value)

    def test_empty_dataframe(self):
        """
        Verify that an empty input DataFrame returns an empty result.
        """
        df = pd.DataFrame(columns=['smiles', 'NR-AR'])
        result = apply_smarts_filter(df, SMARTS_PATTERN)
        assert result.empty
        assert len(result) == 0
