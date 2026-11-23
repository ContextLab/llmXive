"""
Unit tests for the LLSO split generation logic (Task T028).
"""
import pytest
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

from src.data.splits import (
    compute_scaffold_clusters,
    generate_llso_splits,
    save_splits_to_json,
    _hash_scaffold
)


@pytest.fixture
def mock_graphs_df():
    """Create a mock DataFrame with scaffold information."""
    data = {
        'scaffold_smiles': [
            'CC1=CC=CC=C1', # Scaffold A
            'CC1=CC=CC=C1', # Scaffold A
            'CC1=CC=CC=C1', # Scaffold A
            'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', # Scaffold B
            'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', # Scaffold B
            'CC(C)C1=CC=CC=C1', # Scaffold C
            'CC(C)C1=CC=CC=C1', # Scaffold C
            'CC(C)C1=CC=CC=C1', # Scaffold C
            'CC(C)C1=CC=CC=C1', # Scaffold C
            'CC(C)C1=CC=CC=C1'  # Scaffold C
        ],
        'energy_dft': [1.0, 1.1, 1.2, 2.0, 2.1, 3.0, 3.1, 3.2, 3.3, 3.4]
    }
    return pd.DataFrame(data)


def test_hash_scaffold_consistency():
    """Test that identical scaffolds produce the same hash."""
    s1 = "CC1=CC=CC=C1"
    s2 = "CC1=CC=CC=C1"
    s3 = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

    assert _hash_scaffold(s1) == _hash_scaffold(s2)
    assert _hash_scaffold(s1) != _hash_scaffold(s3)


def test_compute_scaffold_clusters(mock_graphs_df):
    """Test that clusters are correctly grouped by scaffold."""
    clusters = compute_scaffold_clusters(mock_graphs_df)

    assert len(clusters) == 3 # A, B, C

    # Check indices for Scaffold A (rows 0, 1, 2)
    # Note: The actual hash depends on the function, but the count should be 3
    found_a = False
    for key, indices in clusters.items():
        if set(indices) == {0, 1, 2}:
            found_a = True
            break
    assert found_a, "Scaffold A indices not found correctly"

    # Check indices for Scaffold B (rows 3, 4)
    found_b = False
    for key, indices in clusters.items():
        if set(indices) == {3, 4}:
            found_b = True
            break
    assert found_b, "Scaffold B indices not found correctly"

    # Check indices for Scaffold C (rows 5-9)
    found_c = False
    for key, indices in clusters.items():
        if set(indices) == {5, 6, 7, 8, 9}:
            found_c = True
            break
    assert found_c, "Scaffold C indices not found correctly"


def test_generate_llso_splits_no_leakage(mock_graphs_df):
    """Test that no scaffold appears in both train and test sets."""
    clusters = compute_scaffold_clusters(mock_graphs_df)
    splits = generate_llso_splits(clusters, n_folds=3, seed=42) # Use 3 folds for simplicity

    # We have 3 clusters. With 3 folds, each fold should have 1 cluster as test.
    for split in splits:
        train_indices = set(split['train_indices'])
        test_indices = set(split['test_indices'])

        # Check intersection is empty
        assert train_indices.isdisjoint(test_indices), "Train and test sets overlap!"

        # Verify all indices are accounted for
        all_indices = set(range(len(mock_graphs_df)))
        assert train_indices.union(test_indices) == all_indices


def test_save_and_load_splits():
    """Test saving splits to JSON and loading them back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "splits.json"
        
        # Dummy splits
        dummy_splits = [
            {"fold": 0, "train_indices": [0, 1], "test_indices": [2]},
            {"fold": 1, "train_indices": [2], "test_indices": [0, 1]}
        ]

        save_splits_to_json(dummy_splits, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            loaded_splits = json.load(f)

        assert loaded_splits == dummy_splits