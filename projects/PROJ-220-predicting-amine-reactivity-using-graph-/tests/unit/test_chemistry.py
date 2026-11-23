"""
Unit tests for src/utils/chemistry.py
"""
import pytest
from rdkit import Chem

from src.utils.chemistry import (
    validate_smiles,
    calculate_gasteiger_charges,
    estimate_pka,
    extract_molecular_features
)


class TestValidateSmiles:
    def test_valid_smiles(self):
        assert validate_smiles("CCO") is True
        assert validate_smiles("c1ccccc1") is True
        assert validate_smiles("N") is True

    def test_invalid_smiles(self):
        assert validate_smiles("invalid") is False
        assert validate_smiles("") is False
        assert validate_smiles(None) is False
        assert validate_smiles("C(") is False

class TestGasteigerCharges:
    def test_ethanol_charges(self):
        mol = Chem.MolFromSmiles("CCO")
        charges = calculate_gasteiger_charges(mol)
        assert charges is not None
        assert len(charges) == mol.GetNumAtoms() + mol.GetNumAtoms() # With hydrogens added

    def test_complex_molecule(self):
        mol = Chem.MolFromSmiles("c1ccccc1O") # Phenol
        charges = calculate_gasteiger_charges(mol)
        assert charges is not None
        assert len(charges) > 0

class TestPKaEstimation:
    def test_primary_amine(self):
        # Methylamine
        pka = estimate_pka("CN")
        assert pka is not None
        assert 10.0 < pka < 11.0

    def test_secondary_amine(self):
        # Dimethylamine
        pka = estimate_pka("CNC")
        assert pka is not None
        assert 10.5 < pka < 11.5

    def test_aniline(self):
        # Aniline
        pka = estimate_pka("Nc1ccccc1")
        assert pka is not None
        assert 4.0 < pka < 5.0

    def test_invalid_input(self):
        assert estimate_pka("invalid") is None
        assert estimate_pka("") is None

class TestExtractFeatures:
    def test_full_extraction(self):
        features = extract_molecular_features("CCN")
        assert features['valid'] is True
        assert features['num_atoms'] > 0
        assert features['charges'] is not None
        assert features['pka'] is not None

    def test_invalid_smiles_extraction(self):
        features = extract_molecular_features("invalid")
        assert features['valid'] is False
        assert features['charges'] is None
        assert features['pka'] is None
        assert features['num_atoms'] == 0
