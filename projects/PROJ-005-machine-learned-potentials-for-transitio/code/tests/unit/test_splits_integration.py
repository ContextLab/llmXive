"""
tests/unit/test_splits_integration.py
Integration tests for LLSO logic in src/data/splits.py and src/models/ensemble.py.

These tests verify that the splits are generated correctly and that the
ensemble training logic integrates with the splits without leakage.
"""
import pytest
import json
import tempfile
from pathlib import Path
import numpy as np

from src.data.splits import generate_llso_splits, compute_scaffold_clusters, save_splits_to_json
from src.models.ensemble import GraphDataset, run_ensemble_training

@pytest.fixture
def mock_graphs_with_scaffolds():
    """
    Creates a mock dataset with known scaffold structures to test LLSO logic.
    Scaffold A: SMILES "C1=CC=CC=C1" (Benzene) - 3 instances
    Scaffold B: SMILES "C1=CC=CN=C1" (Pyridine) - 2 instances
    Scaffold C: SMILES "CC(C)C" (Isobutane) - 2 instances
    """
    return [
        {"ligand_smiles": "C1=CC=CC=C1", "atomic_numbers": [6], "positions": [[0,0,0]], "edge_index": [[0],[0]], "edge_attr": [[0.1]], "barrier_height": 1.0, "id": 0},
        {"ligand_smiles": "C1=CC=CC=C1", "atomic_numbers": [6], "positions": [[0,0,0]], "edge_index": [[0],[0]], "edge_attr": [[0.1]], "barrier_height": 1.1, "id": 1},
        {"ligand_smiles": "C1=CC=CC=C1", "atomic_numbers": [6], "positions": [[0,0,0]], "edge_index": [[0],[0]], "edge_attr": [[0.1]], "barrier_height": 1.2, "id": 2},
        {"ligand_smiles": "C1=CC=CN=C1", "atomic_numbers": [6], "positions": [[0,0,0]], "edge_index": [[0],[0]], "edge_attr": [[0.1]], "barrier_height": 2.0, "id": 3},
        {"ligand_smiles": "C1=CC=CN=C1", "atomic_numbers": [6], "positions": [[0,0,0]], "edge_index": [[0],[0]], "edge_attr": [[0.1]], "barrier_height": 2.1, "id": 4},
        {"ligand_smiles": "CC(C)C", "atomic_numbers": [6], "positions": [[0,0,0]], "edge_index": [[0],[0]], "edge_attr": [[0.1]], "barrier_height": 3.0, "id": 5},
        {"ligand_smiles": "CC(C)C", "atomic_numbers": [6], "positions": [[0,0,0]], "edge_index": [[0],[0]], "edge_attr": [[0.1]], "barrier_height": 3.1, "id": 6},
    ]

def test_compute_scaffold_clusters(mock_graphs_with_scaffolds):
    clusters = compute_scaffold_clusters(mock_graphs_with_scaffolds)
    assert len(clusters) == 3, "Should identify 3 unique scaffolds"
    
    # Check sizes
    sizes = sorted([len(v) for v in clusters.values()])
    assert sizes == [2, 2, 3], "Cluster sizes should match input counts"

def test_generate_llso_splits_no_leakage(mock_graphs_with_scaffolds):
    """
    Tests that no scaffold appears in both train and test for any fold.
    """
    splits = generate_llso_splits(mock_graphs_with_scaffolds, n_folds=3, seed=42)
    
    # We have 3 scaffolds and 3 folds, so each fold should test exactly one scaffold.
    assert len(splits) == 3, "Should generate 3 folds"
    
    for split in splits:
        train_indices = set(split['train_indices'])
        test_indices = set(split['test_indices'])
        
        # Get scaffolds for train and test
        train_scaffolds = set()
        test_scaffolds = set()
        
        for idx in train_indices:
            smiles = mock_graphs_with_scaffolds[idx]['ligand_smiles']
            # Re-calculate scaffold ID to match logic
            import hashlib
            cleaned = smiles.replace(" ", "").lower()
            import re
            cleaned = re.sub(r'\[H\]', '', cleaned)
            cleaned = re.sub(r'H\d*', '', cleaned)
            scaffold_id = hashlib.md5(cleaned.encode('utf-8')).hexdigest()
            train_scaffolds.add(scaffold_id)
            
        for idx in test_indices:
            smiles = mock_graphs_with_scaffolds[idx]['ligand_smiles']
            import hashlib
            cleaned = smiles.replace(" ", "").lower()
            import re
            cleaned = re.sub(r'\[H\]', '', cleaned)
            cleaned = re.sub(r'H\d*', '', cleaned)
            scaffold_id = hashlib.md5(cleaned.encode('utf-8')).hexdigest()
            test_scaffolds.add(scaffold_id)
        
        # Check for intersection
        intersection = train_scaffolds.intersection(test_scaffolds)
        assert len(intersection) == 0, f"Leakage detected in fold! Shared scaffolds: {intersection}"

def test_save_splits_to_json(mock_graphs_with_scaffolds):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_splits.json"
        splits = generate_llso_splits(mock_graphs_with_scaffolds, n_folds=2)
        saved_path = save_splits_to_json(splits, output_path)
        
        assert saved_path.exists(), "File should be saved"
        
        with open(saved_path, 'r') as f:
            loaded = json.load(f)
            
        assert len(loaded) == 2, "Should save 2 folds"
        assert 'train_indices' in loaded[0]
        assert 'test_indices' in loaded[0]

def test_ensemble_training_integration(mock_graphs_with_scaffolds):
    """
    Tests that run_ensemble_training executes without error and produces
    the expected output structure.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        # Run with 2 folds and 1 epoch for speed
        results = run_ensemble_training(
            mock_graphs_with_scaffolds, 
            n_folds=2, 
            epochs=1,
            output_dir=output_dir
        )
        
        assert len(results) == 2, "Should return results for 2 folds"
        for res in results:
            assert 'fold' in res
            assert 'checkpoint_path' in res
            assert Path(res['checkpoint_path']).exists(), "Checkpoint file should exist"
            
        # Check summary file
        summary_path = output_dir / "ensemble_summary.json"
        assert summary_path.exists(), "Summary JSON should exist"