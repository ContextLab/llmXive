"""
Tests for fingerprint generation module.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rdkit import Chem
from code.ingestion.fingerprint import (
    smiles_to_mol,
    generate_ecfp4,
    process_molecule_for_fingerprint,
    get_molecular_weight,
    generate_fingerprints_for_dataset,
    fingerprints_to_bit_vectors,
    FINGERPRINT_BITS,
    FINGERPRINT_RADIUS
)

class TestSmilesToMol:
    """Tests for SMILES to Mol conversion."""

    def test_valid_ethanol(self):
        mol = smiles_to_mol('CCO')
        assert mol is not None
        assert mol.GetNumAtoms() == 3

    def test_valid_benzene(self):
        mol = smiles_to_mol('c1ccccc1')
        assert mol is not None
        assert mol.GetNumAtoms() == 6

    def test_invalid_smiles(self):
        mol = smiles_to_mol('invalid_smiles_string')
        assert mol is None

    def test_empty_string(self):
        mol = smiles_to_mol('')
        assert mol is None

    def test_none_input(self):
        mol = smiles_to_mol(None)
        assert mol is None

class TestGenerateEcfp4:
    """Tests for ECFP4 fingerprint generation."""

    def test_ethanol_fingerprint(self):
        mol = smiles_to_mol('CCO')
        fp = generate_ecfp4(mol)
        assert fp is not None
        assert len(fp) > 0
        assert all(0 <= idx < FINGERPRINT_BITS for idx in fp)

    def test_benzene_fingerprint(self):
        mol = smiles_to_mol('c1ccccc1')
        fp = generate_ecfp4(mol)
        assert fp is not None
        assert len(fp) > 0

    def test_different_molecules_different_fingerprints(self):
        mol1 = smiles_to_mol('CCO')
        mol2 = smiles_to_mol('c1ccccc1')
        fp1 = generate_ecfp4(mol1)
        fp2 = generate_ecfp4(mol2)
        assert fp1 != fp2

class TestMolecularWeight:
    """Tests for molecular weight calculation."""

    def test_ethanol_mw(self):
        mol = smiles_to_mol('CCO')
        mw = get_molecular_weight(mol)
        assert 45.0 <= mw <= 47.0  # Ethanol MW is ~46 g/mol

    def test_benzene_mw(self):
        mol = smiles_to_mol('c1ccccc1')
        mw = get_molecular_weight(mol)
        assert 77.0 <= mw <= 79.0  # Benzene MW is ~78 g/mol

class TestProcessMoleculeForFingerprint:
    """Tests for molecule processing with fingerprint generation."""

    def test_normal_molecule(self):
        mol = smiles_to_mol('CCO')
        result = process_molecule_for_fingerprint(mol, 'CCO')
        assert result is not None
        fp_indices, mw = result
        assert len(fp_indices) > 0
        assert 45.0 <= mw <= 47.0

    def test_large_molecule_skipped(self):
        # Create a very large molecule (polymer-like)
        large_smiles = 'CC' * 500  # Very long chain
        mol = smiles_to_mol(large_smiles)
        if mol is not None:
            result = process_molecule_for_fingerprint(mol, large_smiles, mw_threshold=100.0)
            assert result is None  # Should be skipped due to MW threshold

class TestFingerprintsToBitVectors:
    """Tests for converting fingerprint indices to bit vectors."""

    def test_basic_conversion(self):
        fp_list = [[1, 5, 10], [2, 3, 100]]
        vectors = fingerprints_to_bit_vectors(fp_list, n_bits=10)
        assert len(vectors) == 2
        assert len(vectors[0]) == 10
        assert vectors[0][1] == 1
        assert vectors[0][5] == 1
        assert vectors[0][10] == 0  # Out of bounds
        assert vectors[0][0] == 0

    def test_empty_fingerprints(self):
        fp_list = [[], []]
        vectors = fingerprints_to_bit_vectors(fp_list, n_bits=5)
        assert vectors == [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]

class TestGenerateFingerprintsForDataset:
    """Tests for batch fingerprint generation."""

    def test_batch_processing(self):
        molecules = [
            {'smiles': 'CCO', 'space_group': 'P21/c'},
            {'smiles': 'c1ccccc1', 'space_group': 'P1'},
            {'smiles': 'CC(=O)O', 'space_group': 'P21'}
        ]
        results = generate_fingerprints_for_dataset(molecules)
        assert len(results) == 3
        for record in results:
            assert 'fingerprint_indices' in record
            assert 'molecular_weight' in record

    def test_skips_invalid_smiles(self):
        molecules = [
            {'smiles': 'CCO', 'space_group': 'P21/c'},
            {'smiles': 'invalid', 'space_group': 'P1'},
            {'smiles': 'c1ccccc1', 'space_group': 'P21'}
        ]
        results = generate_fingerprints_for_dataset(molecules)
        # Should only have 2 valid results
        assert len(results) == 2

    def test_empty_dataset(self):
        results = generate_fingerprints_for_dataset([])
        assert len(results) == 0