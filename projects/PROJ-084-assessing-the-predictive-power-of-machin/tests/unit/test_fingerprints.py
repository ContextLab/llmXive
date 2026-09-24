"""
Unit tests for fingerprint generation module.
Tests T016: Verify ECFP4=2048 and MACCS=167 dimensions.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing.fingerprints import (
    generate_ecfp4,
    generate_maccs,
    generate_fingerprints_batch,
    ECFP_BITS,
    MACCS_BITS
)
from utils.validators import validate_fingerprint_dimensions


class TestFingerprintDimensions:
    """Test that fingerprints have correct dimensions."""
    
    def test_ecfp4_dimension(self):
        """Verify ECFP4 fingerprint has exactly 2048 bits."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        fp = generate_ecfp4(smiles)
        
        assert len(fp) == ECFP_BITS, f"ECFP4 length {len(fp)} != {ECFP_BITS}"
        assert all(isinstance(x, int) for x in fp), "ECFP4 should contain integers"
        assert all(x in [0, 1] for x in fp), "ECFP4 should be binary (0 or 1)"
    
    def test_maccs_dimension(self):
        """Verify MACCS fingerprint has exactly 167 bits."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        fp = generate_maccs(smiles)
        
        assert len(fp) == MACCS_BITS, f"MACCS length {len(fp)} != {MACCS_BITS}"
        assert all(isinstance(x, int) for x in fp), "MACCS should contain integers"
        assert all(x in [0, 1] for x in fp), "MACCS should be binary (0 or 1)"
    
    def test_ecfp4_different_molecules(self):
        """Verify ECFP4 dimensions are consistent across different molecules."""
        smiles_list = [
            "CCO",  # Ethanol
            "CC(=O)O",  # Acetic acid
            "c1ccccc1",  # Benzene
            "CC1=CC=CC=C1",  # Toluene
            "CC(C)C(C(=O)O)NC(=O)C1=CC=CC=C1"  # Phenylalanine derivative
        ]
        
        for smiles in smiles_list:
            fp = generate_ecfp4(smiles)
            assert len(fp) == ECFP_BITS, f"Failed for {smiles}: {len(fp)} != {ECFP_BITS}"
    
    def test_maccs_different_molecules(self):
        """Verify MACCS dimensions are consistent across different molecules."""
        smiles_list = [
            "CCO",
            "CC(=O)O",
            "c1ccccc1",
            "CC1=CC=CC=C1",
            "CC(C)C(C(=O)O)NC(=O)C1=CC=CC=C1"
        ]
        
        for smiles in smiles_list:
            fp = generate_maccs(smiles)
            assert len(fp) == MACCS_BITS, f"Failed for {smiles}: {len(fp)} != {MACCS_BITS}"


class TestFingerprintValidation:
    """Test fingerprint validation logic."""
    
    def test_validate_ecfp_dimensions(self):
        """Test validation of ECFP dimensions."""
        valid_fp = [0] * ECFP_BITS
        validate_fingerprint_dimensions(valid_fp, ECFP_BITS, "ECFP")  # Should not raise
        
        invalid_fp = [0] * (ECFP_BITS - 1)
        with pytest.raises(ValueError):
            validate_fingerprint_dimensions(invalid_fp, ECFP_BITS, "ECFP")
    
    def test_validate_maccs_dimensions(self):
        """Test validation of MACCS dimensions."""
        valid_fp = [0] * MACCS_BITS
        validate_fingerprint_dimensions(valid_fp, MACCS_BITS, "MACCS")  # Should not raise
        
        invalid_fp = [0] * (MACCS_BITS - 1)
        with pytest.raises(ValueError):
            validate_fingerprint_dimensions(invalid_fp, MACCS_BITS, "MACCS")


class TestBatchProcessing:
    """Test batch fingerprint generation."""
    
    def test_generate_fingerprints_batch(self):
        """Test batch generation of fingerprints."""
        data = {
            'smiles': [
                "CCO",
                "CC(=O)O",
                "c1ccccc1"
            ],
            'yield': [80.0, 90.0, 75.0],
            'reaction_class': ['hydrolysis', 'oxidation', 'reduction']
        }
        df = pd.DataFrame(data)
        
        result = generate_fingerprints_batch(df)
        
        assert 'fingerprint_ecfp' in result.columns
        assert 'fingerprint_maccs' in result.columns
        assert len(result) == len(df)
        
        # Check dimensions
        for idx, row in result.iterrows():
            assert len(row['fingerprint_ecfp']) == ECFP_BITS
            assert len(row['fingerprint_maccs']) == MACCS_BITS
    
    def test_batch_with_invalid_smiles(self):
        """Test batch processing with invalid SMILES."""
        data = {
            'smiles': [
                "CCO",
                "INVALID_SMILES",
                "c1ccccc1"
            ],
            'yield': [80.0, 90.0, 75.0],
            'reaction_class': ['hydrolysis', 'oxidation', 'reduction']
        }
        df = pd.DataFrame(data)
        
        result = generate_fingerprints_batch(df)
        
        # Should have None for invalid SMILES
        assert result.loc[1, 'fingerprint_ecfp'] is None
        assert result.loc[1, 'fingerprint_maccs'] is None
        
        # Valid ones should have fingerprints
        assert result.loc[0, 'fingerprint_ecfp'] is not None
        assert result.loc[2, 'fingerprint_ecfp'] is not None


class TestConstants:
    """Test module constants."""
    
    def test_ecfp_bits_constant(self):
        """Verify ECFP_BITS constant is 2048."""
        assert ECFP_BITS == 2048
    
    def test_maccs_bits_constant(self):
        """Verify MACCS_BITS constant is 167."""
        assert MACCS_BITS == 167