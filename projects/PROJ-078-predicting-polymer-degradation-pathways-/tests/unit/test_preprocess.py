"""
Unit tests for preprocessing functions.
"""
import pytest
import pandas as pd
from pathlib import Path

from preprocess import is_polyester, filter_polyesters, canonicalize_smiles

class TestPolyesterDetection:
    """Tests for polyester functional group detection."""
    
    def test_is_polyester_true(self):
        """Test detection of valid polyester SMILES."""
        # Polyethylene terephthalate (PET) monomer unit
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        assert is_polyester(smiles) is True
        
        # Polylactic acid (PLA)
        smiles_pla = "CC(C(=O)O)O"
        assert is_polyester(smiles_pla) is True
    
    def test_is_polyester_false(self):
        """Test rejection of non-polyester SMILES."""
        # Alkane
        assert is_polyester("CCCCC") is False
        
        # Alcohol
        assert is_polyester("CCO") is False
        
        # Alkene
        assert is_polyester("CC=C") is False
        
        # Ether (no carbonyl)
        assert is_polyester("COCC") is False
    
    def test_is_polyester_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        assert is_polyester("invalid_smiles") is False
        assert is_polyester("") is False
    
    def test_filter_polyesters(self):
        """Test the filter_polyesters function."""
        records = [
            {'id': '1', 'smiles': 'CC(=O)Oc1ccccc1C(=O)O'},  # Polyester
            {'id': '2', 'smiles': 'CCCCC'},  # Not polyester
            {'id': '3', 'smiles': 'CC(C(=O)O)O'},  # Polyester
            {'id': '4', 'smiles': 'CCO'},  # Not polyester
        ]
        
        polyesters, non_polyesters = filter_polyesters(records)
        
        assert len(polyesters) == 2
        assert len(non_polyesters) == 2
        
        polyester_ids = [r['id'] for r in polyesters]
        assert '1' in polyester_ids
        assert '3' in polyester_ids
        
        non_polyester_ids = [r['id'] for r in non_polyesters]
        assert '2' in non_polyester_ids
        assert '4' in non_polyester_ids

class TestCanonicalizeSmiles:
    """Tests for SMILES canonicalization."""
    
    def test_canonicalize_valid(self):
        """Test canonicalization of valid SMILES."""
        smiles = "CCO"
        canonical = canonicalize_smiles(smiles)
        assert canonical is not None
        assert isinstance(canonical, str)
    
    def test_canonicalize_invalid(self):
        """Test handling of invalid SMILES."""
        assert canonicalize_smiles("invalid") is None
        assert canonicalize_smiles("") is None