import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

from fingerprints import (
    generate_morgan_fingerprint,
    generate_maccs_fingerprint,
    calculate_tanimoto_similarity,
    generate_fingerprints_batch
)

class TestMorganFingerprint:
    def test_morgan_fingerprint_generation(self):
        """Test that Morgan fingerprint is generated correctly."""
        smiles = "CCO"  # Ethanol
        fp = generate_morgan_fingerprint(smiles)
        
        assert fp is not None
        assert fp.GetNumBits() == 2048
        assert fp.GetNumOnBits() > 0
    
    def test_morgan_fingerprint_invalid_smiles(self):
        """Test that invalid SMILES returns None."""
        invalid_smiles = "invalid_smiles_string"
        fp = generate_morgan_fingerprint(invalid_smiles)
        assert fp is None

class TestMACCSFingerprint:
    def test_maccs_fingerprint_generation(self):
        """Test that MACCS fingerprint is generated correctly."""
        smiles = "CCO"  # Ethanol
        fp = generate_maccs_fingerprint(smiles)
        
        assert fp is not None
        assert fp.GetNumBits() == 166
        assert fp.GetNumOnBits() > 0
    
    def test_maccs_fingerprint_invalid_smiles(self):
        """Test that invalid SMILES returns None."""
        invalid_smiles = "invalid_smiles_string"
        fp = generate_maccs_fingerprint(invalid_smiles)
        assert fp is None

class TestTanimotoSimilarity:
    def test_tanimoto_similarity(self):
        """Test Tanimoto similarity calculation."""
        smiles1 = "CCO"
        smiles2 = "CCO"
        
        fp1 = generate_morgan_fingerprint(smiles1)
        fp2 = generate_morgan_fingerprint(smiles2)
        
        similarity = calculate_tanimoto_similarity(fp1, fp2)
        
        # Identical molecules should have similarity of 1.0
        assert similarity == 1.0
    
    def test_tanimoto_similarity_different(self):
        """Test Tanimoto similarity for different molecules."""
        smiles1 = "CCO"
        smiles2 = "CCCC"
        
        fp1 = generate_morgan_fingerprint(smiles1)
        fp2 = generate_morgan_fingerprint(smiles2)
        
        similarity = calculate_tanimoto_similarity(fp1, fp2)
        
        # Different molecules should have similarity < 1.0
        assert similarity < 1.0
        assert similarity >= 0.0
    
    def test_tanimoto_similarity_none(self):
        """Test Tanimoto similarity with None fingerprints."""
        similarity = calculate_tanimoto_similarity(None, None)
        assert similarity == 0.0

class TestBatchGeneration:
    def test_generate_fingerprints_batch(self):
        """Test batch fingerprint generation."""
        smiles_list = ["CCO", "CCCC", "CC(=O)O"]
        
        fps, failed = generate_fingerprints_batch(smiles_list, fp_type="morgan")
        
        assert len(fps) == len(smiles_list)
        assert len(failed) == 0
        assert fps.shape == (len(smiles_list), 2048)
    
    def test_generate_fingerprints_batch_with_invalid(self):
        """Test batch generation with some invalid SMILES."""
        smiles_list = ["CCO", "invalid", "CCCC"]
        
        fps, failed = generate_fingerprints_batch(smiles_list, fp_type="morgan")
        
        assert len(fps) == 2
        assert len(failed) == 1
        assert "invalid" in failed
        assert fps.shape == (2, 2048)