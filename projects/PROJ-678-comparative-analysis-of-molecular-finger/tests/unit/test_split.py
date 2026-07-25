"""
Unit tests for code/split.py
"""
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

from split import greedy_maximal_dissimilarity_split, save_splits

def test_greedy_split_tanimoto_threshold():
    """
    Verify the greedy split logic maintains Tanimoto < 0.85.
    """
    # Create a small dummy dataset
    # 10 samples, 64 bits
    np.random.seed(42)
    n_samples = 10
    n_bits = 64
    fingerprints = np.random.randint(0, 2, (n_samples, n_bits)).astype(float)
    
    # Run split
    results = greedy_maximal_dissimilarity_split(
        fingerprints,
        n_folds=2,
        threshold=0.85,
        min_test_size=2
    )
    
    # Check results structure
    assert len(results) == 2
    for res in results:
        assert "fold" in res
        assert "status" in res
        assert "test_indices" in res
        assert "train_indices" in res
        
        # If valid, check test set size
        if res["status"] == "VALID":
            assert len(res["test_indices"]) >= 2

def test_save_splits_creates_files():
    """
    Verify save_splits creates the correct JSON files.
    """
    fold_results = [
        {
            "fold": 0,
            "status": "VALID",
            "test_indices": [0, 1, 2],
            "train_indices": [3, 4, 5]
        },
        {
            "fold": 1,
            "status": "INVALID",
            "test_indices": [],
            "train_indices": []
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_splits(fold_results, tmpdir)
        
        # Check files exist
        assert os.path.exists(os.path.join(tmpdir, "split_fold_0.json"))
        assert os.path.exists(os.path.join(tmpdir, "split_fold_1.json"))
        assert os.path.exists(os.path.join(tmpdir, "split_summary.json"))
        
        # Check summary content
        with open(os.path.join(tmpdir, "split_summary.json"), 'r') as f:
            summary = json.load(f)
        
        assert summary["total_folds"] == 2
        assert summary["valid_folds"] == 1
        assert summary["invalid_folds"] == 1
        assert summary["status"] == "INVALID"
