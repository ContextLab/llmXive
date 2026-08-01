"""
Unit tests for fingerprint dimensionality.
"""

import pytest
import numpy as np
from rdkit import Chem
from preprocessing.fingerprints import generate_ecfp4, generate_maccs

class TestECFP4:
    def test_ecfp4_dimensionality(self):
        """Test that ECFP4 fingerprint has correct dimensionality (2048)."""
        mol = Chem.MolFromSmiles("CCO")
        fp = generate_ecfp4(mol)
        assert len(fp) == 2048
        assert fp.dtype == np.uint8

    def test_ecfp4_empty_molecule(self):
        """Test ECFP4 for None molecule."""
        fp = generate_ecfp4(None)
        assert len(fp) == 2048
        assert np.all(fp == 0)

    def test_ecfp4_values_binary(self):
        """Test that ECFP4 values are binary (0 or 1)."""
        mol = Chem.MolFromSmiles("CCO")
        fp = generate_ecfp4(mol)
        assert np.all((fp == 0) | (fp == 1))

class TestMACCS:
    def test_maccs_dimensionality(self):
        """Test that MACCS fingerprint has correct dimensionality (167)."""
        mol = Chem.MolFromSmiles("CCO")
        fp = generate_maccs(mol)
        assert len(fp) == 167
        assert fp.dtype == np.uint8

    def test_maccs_empty_molecule(self):
        """Test MACCS for None molecule."""
        fp = generate_maccs(None)
        assert len(fp) == 167
        assert np.all(fp == 0)

    def test_maccs_values_binary(self):
        """Test that MACCS values are binary (0 or 1)."""
        mol = Chem.MolFromSmiles("CCO")
        fp = generate_maccs(mol)
        assert np.all((fp == 0) | (fp == 1))
