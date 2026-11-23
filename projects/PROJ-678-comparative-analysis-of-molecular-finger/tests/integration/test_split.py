"""
Integration tests for the split module.
"""
import pytest
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from split import (
    calculate_tanimoto_distance,
    greedy_maximal_dissimilarity_split,
    verify_split_summary
)
from fingerprints import generate_morgan_fingerprint
from constants import TANIMOTO_THRESHOLD, MORGAN_RADIUS, MORGAN_BITS


def test_tanimoto_distance_calculation():
    """Test that Tanimoto distance is correctly calculated."""
    # Create two simple molecules
    mol1 = Chem.MolFromSmiles("CCO")
    mol2 = Chem.MolFromSmiles("CCCO")
    
    fp1 = generate_morgan_fingerprint(mol1, radius=MORGAN_RADIUS, nBits=MORGAN_BITS)
    fp2 = generate_morgan_fingerprint(mol2, radius=MORGAN_RADIUS, nBits=MORGAN_BITS)
    
    # Distance should be between 0 and 1
    distance = calculate_tanimoto_distance(fp1, fp2)
    assert 0.0 <= distance <= 1.0
    
    # Distance should be symmetric
    distance_sym = calculate_tanimoto_distance(fp2, fp1)
    assert distance == distance_sym
    
    # Distance to self should be 0
    distance_self = calculate_tanimoto_distance(fp1, fp1)
    assert distance_self == 0.0


def test_greedy_split_creates_valid_sets():
    """Test that greedy split creates non-overlapping train/test sets."""
    # Create a small dataset
    smiles_list = [
        "CCO", "CCCO", "CCCCO", "CC(C)O", "CC(C)CO",
        "C1=CC=CC=C1", "C1=CC=CC=C1O", "C1=CC=CC=C1N",
        "CC(=O)O", "CCC(=O)O", "CCCC(=O)O", "CC(C)(C)O",
        "CC(C)(C)CO", "CC(C)(C)CCO", "CC(C)(C)CCC",
        "C1CC1", "C1CCC1", "C1CCCC1", "C1CCCCC1", "C1CCCCCC1"
    ]
    
    fingerprints = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        fp = generate_morgan_fingerprint(mol, radius=MORGAN_RADIUS, nBits=MORGAN_BITS)
        fingerprints.append(fp)
    
    # Perform split with small test size
    train_indices, test_indices = greedy_maximal_dissimilarity_split(
        fingerprints,
        tanimoto_threshold=0.85,
        test_fraction=0.3,
        min_test_size=3
    )
    
    # Check that sets are non-overlapping
    assert set(train_indices).isdisjoint(set(test_indices))
    
    # Check that union equals all indices
    all_indices = set(range(len(fingerprints)))
    assert set(train_indices).union(set(test_indices)) == all_indices
    
    # Check that test set meets minimum size
    assert len(test_indices) >= 3


def test_greedy_split_respects_tanimoto_threshold():
    """Test that split respects Tanimoto threshold constraint."""
    # Create a diverse dataset
    smiles_list = [
        "CCO", "CCCCCCCCCCCCCCCCO",  # Very different chain lengths
        "C1=CC=CC=C1", "C1=CC=CC=C1O",  # Aromatic
        "CC(=O)O", "CCCCCCCC(=O)O",  # Aliphatic acids
        "C1CC1", "C1CCCCC1",  # Cyclic
        "CC(C)(C)O", "CC(C)(C)CC(C)(C)O",  # Branched
        "CN(C)C", "CCN(C)C",  # Amines
        "CC(=O)N", "CCC(=O)N",  # Amides
        "CS(=O)(=O)O", "CCCCS(=O)(=O)O",  # Sulfonic acids
        "C1=CC=C(C=C1)O", "C1=CC=C(C=C1)N",  # Substituted aromatics
        "C1CC1O", "C1CCCC1O"  # Cyclic alcohols
    ]
    
    fingerprints = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        fp = generate_morgan_fingerprint(mol, radius=MORGAN_RADIUS, nBits=MORGAN_BITS)
        fingerprints.append(fp)
    
    # Perform split
    train_indices, test_indices = greedy_maximal_dissimilarity_split(
        fingerprints,
        tanimoto_threshold=TANIMOTO_THRESHOLD,
        test_fraction=0.3,
        min_test_size=5
    )
    
    # Verify no violations
    max_sim = 0.0
    for test_idx in test_indices:
        for train_idx in train_indices:
            sim = DataStructs.TanimotoSimilarity(fingerprints[test_idx], fingerprints[train_idx])
            if sim > max_sim:
                max_sim = sim
    
    # The split should respect the threshold (or be as close as possible)
    # Note: In some cases with small datasets, perfect separation may not be possible
    # but the algorithm should minimize violations
    assert max_sim <= TANIMOTO_THRESHOLD + 0.01  # Allow small numerical tolerance


def test_verify_split_summary():
    """Test the verification function."""
    # Create simple fingerprints
    smiles_list = ["CCO", "CCCO", "CCCCO", "C1=CC=CC=C1", "C1=CC=CC=C1O"]
    fingerprints = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        fp = generate_morgan_fingerprint(mol, radius=MORGAN_RADIUS, nBits=MORGAN_BITS)
        fingerprints.append(fp)
    
    train_indices = [0, 1, 2]
    test_indices = [3, 4]
    
    verification = verify_split_summary(
        fingerprints,
        train_indices,
        test_indices,
        tanimoto_threshold=TANIMOTO_THRESHOLD
    )
    
    # Check structure
    assert "status" in verification
    assert "test_size" in verification
    assert "train_size" in verification
    assert "tanimoto_min" in verification
    assert "tanimoto_max" in verification
    
    # Check values
    assert verification["test_size"] == 2
    assert verification["train_size"] == 3
    assert verification["train_size"] + verification["test_size"] == len(fingerprints)


def test_split_with_min_test_size():
    """Test that minimum test size is enforced."""
    # Create a small dataset
    smiles_list = ["CCO", "CCCO", "CCCCO", "C1=CC=CC=C1", "C1=CC=CC=C1O"]
    fingerprints = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        fp = generate_morgan_fingerprint(mol, radius=MORGAN_RADIUS, nBits=MORGAN_BITS)
        fingerprints.append(fp)
    
    # Request a test set of at least 3
    train_indices, test_indices = greedy_maximal_dissimilarity_split(
        fingerprints,
        tanimoto_threshold=TANIMOTO_THRESHOLD,
        test_fraction=0.1,  # Would normally give 0.5
        min_test_size=3
    )
    
    # Should have at least 3 in test set
    assert len(test_indices) >= 3