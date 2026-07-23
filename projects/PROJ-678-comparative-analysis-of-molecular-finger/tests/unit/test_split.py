"""
Unit tests for the greedy maximal dissimilarity split logic.
"""
import pytest
import numpy as np
from rdkit import DataStructs
from rdkit import Chem
from rdkit.Chem import AllChem
import sys
import os

# Add the project root to the path to import code modules
# Assuming tests are at tests/unit/ and code is at code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.split import greedy_maximal_dissimilarity_split
from code.constants import TANIMOTO_THRESHOLD


def create_mock_fingerprints(n_compounds, n_bits=2048, radius=2):
    """
    Create a list of mock Morgan fingerprints for testing.
    Generates random bit vectors to simulate fingerprint data.
    """
    fps = []
    for _ in range(n_compounds):
        # Create a random molecule to generate a real fingerprint
        # This ensures we use RDKit's fingerprint logic, not just random bits
        mol = Chem.MolFromSmiles("CC" * 10) # Ethane chain, simple
        if mol is None:
            # Fallback if smile parsing fails (unlikely)
            fp = DataStructs.ExplicitBitVect(n_bits)
            # Set random bits
            for i in range(10):
                fp.SetBit(np.random.randint(0, n_bits))
        else:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        fps.append(fp)
    return fps


def test_greedy_split_tanimoto_threshold():
    """
    Verify the greedy split logic maintains Tanimoto < 0.85 between test set members.
    
    This test:
    1. Generates a set of mock fingerprints.
    2. Runs the greedy maximal dissimilarity split.
    3. Iterates through the resulting test set indices.
    4. Calculates pairwise Tanimoto similarities.
    5. Asserts that all pairwise similarities are strictly less than TANIMOTO_THRESHOLD.
    """
    # Configuration
    n_compounds = 50
    n_folds = 1
    n_bits = 2048
    radius = 2
    threshold = TANIMOTO_THRESHOLD # Should be 0.85 from constants
    
    # Create mock data
    fingerprints = create_mock_fingerprints(n_compounds, n_bits, radius)
    
    # Run the split
    # The function signature expects (fingerprints, n_folds, threshold)
    # It returns a list of dicts, each containing 'train_indices' and 'test_indices'
    try:
        split_result = greedy_maximal_dissimilarity_split(fingerprints, n_folds, threshold)
    except Exception as e:
        # If the split fails (e.g., not enough diversity), we should still verify
        # that if it returns a result, it meets the criteria. 
        # However, for this unit test, we assume we have enough compounds.
        # If it raises, it might be due to insufficient data for the threshold.
        pytest.fail(f"Greedy split raised an exception: {e}")

    # Verify the result structure
    assert isinstance(split_result, list), "Split result should be a list of fold dicts"
    assert len(split_result) == n_folds, f"Expected {n_folds} folds, got {len(split_result)}"

    fold_data = split_result[0]
    test_indices = fold_data['test_indices']
    
    assert len(test_indices) > 0, "Test set should not be empty"
    
    # Check pairwise Tanimoto similarity
    # We need to ensure that for any two compounds in the test set,
    # their Tanimoto similarity is < threshold.
    # Note: The greedy algorithm selects compounds that are MAXIMALLY dissimilar
    # to the current set. If the threshold is set, it should enforce this.
    
    # Optimization: If test set is small, just check all pairs.
    # If large, we can sample, but for unit test n_compounds=50, it's fine.
    
    for i in range(len(test_indices)):
        for j in range(i + 1, len(test_indices)):
            idx_i = test_indices[i]
            idx_j = test_indices[j]
            
            fp_i = fingerprints[idx_i]
            fp_j = fingerprints[idx_j]
            
            tanimoto = DataStructs.TanimotoSimilarity(fp_i, fp_j)
            
            # Assert that the similarity is strictly less than the threshold
            # Use a small epsilon for float comparison safety if needed, 
            # but strict < is the requirement.
            assert tanimoto < threshold, (
                f"Pairwise Tanimoto similarity {tanimoto:.4f} between indices "
                f"{idx_i} and {idx_j} exceeds threshold {threshold}. "
                "Greedy split failed to maintain diversity."
            )


def test_greedy_split_min_test_size():
    """
    Verify the greedy split produces a test set of at least size 20.
    """
    n_compounds = 100
    n_folds = 1
    n_bits = 2048
    radius = 2
    threshold = TANIMOTO_THRESHOLD
    
    fingerprints = create_mock_fingerprints(n_compounds, n_bits, radius)
    
    try:
        split_result = greedy_maximal_dissimilarity_split(fingerprints, n_folds, threshold)
    except Exception as e:
        pytest.fail(f"Greedy split raised an exception: {e}")
    
    fold_data = split_result[0]
    test_indices = fold_data['test_indices']
    
    assert len(test_indices) >= 20, (
        f"Test set size {len(test_indices)} is less than the minimum required 20. "
        "This indicates insufficient structural diversity or a logic error."
    )


def test_greedy_split_disjoint_sets():
    """
    Verify that train and test sets are disjoint for a fold.
    """
    n_compounds = 100
    n_folds = 1
    n_bits = 2048
    radius = 2
    threshold = TANIMOTO_THRESHOLD
    
    fingerprints = create_mock_fingerprints(n_compounds, n_bits, radius)
    
    try:
        split_result = greedy_maximal_dissimilarity_split(fingerprints, n_folds, threshold)
    except Exception as e:
        pytest.fail(f"Greedy split raised an exception: {e}")
    
    fold_data = split_result[0]
    train_indices = set(fold_data['train_indices'])
    test_indices = set(fold_data['test_indices'])
    
    intersection = train_indices.intersection(test_indices)
    assert len(intersection) == 0, (
        f"Train and test sets are not disjoint. Intersection: {intersection}"
    )