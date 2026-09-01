"""
Unit tests for fingerprint generation module.
Tests T013 requirement: Verify ECFP4=2048, MACCS=167 dimensions.
"""
import numpy as np
import pytest
from rdkit import Chem

from preprocessing.fingerprints import (
    generate_ecfp4,
    generate_maccs,
    ECFP4_BITS,
    MACCS_BITS,
)


def test_ecfp4_dimensionality():
    """Test that ECFP4 fingerprints have exactly 2048 bits."""
    smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
    fp = generate_ecfp4(smiles)

    assert fp is not None, "ECFP4 generation failed for valid SMILES"
    assert isinstance(fp, np.ndarray), "ECFP4 should return numpy array"
    assert fp.dtype == np.int8, f"ECFP4 dtype should be int8, got {fp.dtype}"
    assert len(fp) == ECFP4_BITS, f"ECFP4 length should be {ECFP4_BITS}, got {len(fp)}"


def test_maccs_dimensionality():
    """Test that MACCS fingerprints have exactly 167 bits."""
    smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
    fp = generate_maccs(smiles)

    assert fp is not None, "MACCS generation failed for valid SMILES"
    assert isinstance(fp, np.ndarray), "MACCS should return numpy array"
    assert fp.dtype == np.int8, f"MACCS dtype should be int8, got {fp.dtype}"
    assert len(fp) == MACCS_BITS, f"MACCS length should be {MACCS_BITS}, got {len(fp)}"


def test_ecfp4_binary_values():
    """Test that ECFP4 contains only 0 and 1 values."""
    smiles = "CCO"  # Ethanol
    fp = generate_ecfp4(smiles)

    assert fp is not None
    unique_values = np.unique(fp)
    assert set(unique_values).issubset({0, 1}), "ECFP4 should contain only 0 and 1"


def test_maccs_binary_values():
    """Test that MACCS contains only 0 and 1 values."""
    smiles = "CCO"  # Ethanol
    fp = generate_maccs(smiles)

    assert fp is not None
    unique_values = np.unique(fp)
    assert set(unique_values).issubset({0, 1}), "MACCS should contain only 0 and 1"


def test_invalid_smiles_returns_none():
    """Test that invalid SMILES returns None."""
    invalid_smiles = "invalid_smiles_string_12345"

    ecfp4_fp = generate_ecfp4(invalid_smiles)
    maccs_fp = generate_maccs(invalid_smiles)

    assert ecfp4_fp is None, "ECFP4 should return None for invalid SMILES"
    assert maccs_fp is None, "MACCS should return None for invalid SMILES"


def test_empty_smiles_returns_none():
    """Test that empty SMILES returns None."""
    empty_smiles = ""

    ecfp4_fp = generate_ecfp4(empty_smiles)
    maccs_fp = generate_maccs(empty_smiles)

    assert ecfp4_fp is None
    assert maccs_fp is None


def test_consistency_same_molecule():
    """Test that same SMILES produces same fingerprint."""
    smiles = "CCO"

    fp1_ecfp = generate_ecfp4(smiles)
    fp2_ecfp = generate_ecfp4(smiles)

    fp1_maccs = generate_maccs(smiles)
    fp2_maccs = generate_maccs(smiles)

    assert np.array_equal(fp1_ecfp, fp2_ecfp), "ECFP4 should be deterministic"
    assert np.array_equal(fp1_maccs, fp2_maccs), "MACCS should be deterministic"


def test_different_molecules_different_fingerprints():
    """Test that different molecules produce different fingerprints."""
    smiles1 = "CCO"  # Ethanol
    smiles2 = "CCCO"  # Propanol

    fp1_ecfp = generate_ecfp4(smiles1)
    fp2_ecfp = generate_ecfp4(smiles2)

    fp1_maccs = generate_maccs(smiles1)
    fp2_maccs = generate_maccs(smiles2)

    # They should not be identical
    assert not np.array_equal(fp1_ecfp, fp2_ecfp), "Different molecules should have different ECFP4"
    assert not np.array_equal(fp1_maccs, fp2_maccs), "Different molecules should have different MACCS"


def test_ecfp4_sparse():
    """Test that ECFP4 fingerprints are sparse (mostly zeros)."""
    # Use a moderately complex molecule
    smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
    fp = generate_ecfp4(smiles)

    assert fp is not None
    non_zero_count = np.sum(fp)
    total_count = len(fp)
    sparsity = 1.0 - (non_zero_count / total_count)

    # ECFP4 should be sparse (>90% zeros for typical molecules)
    assert sparsity > 0.90, f"ECFP4 should be sparse, got {sparsity:.2%} zeros"


def test_maccs_sparse():
    """Test that MACCS fingerprints are sparse."""
    smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
    fp = generate_maccs(smiles)

    assert fp is not None
    non_zero_count = np.sum(fp)
    total_count = len(fp)
    sparsity = 1.0 - (non_zero_count / total_count)

    # MACCS should also be sparse
    assert sparsity > 0.50, f"MACCS should be sparse, got {sparsity:.2%} zeros"
