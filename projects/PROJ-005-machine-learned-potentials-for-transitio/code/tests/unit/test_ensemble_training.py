"""
tests/unit/test_ensemble_training.py

Unit tests for the LLSO split generation and ensemble training logic.
"""
import pytest
import pandas as pd
import numpy as np
import torch
from pathlib import Path
import tempfile
import json

from src.data.splits import (
    load_graphs_for_splitting,
    compute_scaffold_clusters,
    generate_llso_splits,
    save_splits_to_json
)
from src.models.ensemble import GraphDataset, set_seed

def test_compute_scaffold_clusters():
    """Test that scaffolds are correctly grouped."""
    data = {
        'ligand_scaffold': ['A', 'A', 'B', 'B', 'B', 'C'],
        'graph_id': [0, 1, 2, 3, 4, 5]
    }
    df = pd.DataFrame(data)
    
    clusters = compute_scaffold_clusters(df)
    
    assert 'A' in clusters
    assert 'B' in clusters
    assert 'C' in clusters
    assert set(clusters['A']) == {0, 1}
    assert set(clusters['B']) == {2, 3, 4}
    assert set(clusters['C']) == {5}

def test_generate_llso_splits_no_overlap():
    """Test that train and test sets share no scaffolds."""
    data = {
        'ligand_scaffold': ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'E', 'E'],
        'graph_id': list(range(10))
    }
    df = pd.DataFrame(data)
    clusters = compute_scaffold_clusters(df)
    
    splits = generate_llso_splits(clusters, n_folds=5, seed=42)
    
    for split in splits:
        train_scaffolds = set(split['train_scaffolds'])
        test_scaffolds = set(split['test_scaffolds'])
        
        # Check intersection is empty
        assert len(train_scaffolds.intersection(test_scaffolds)) == 0
        
        # Check all scaffolds are covered
        all_scaffolds = set(clusters.keys())
        assert train_scaffolds.union(test_scaffolds) == all_scaffolds

def test_graph_dataset_creation():
    """Test that GraphDataset can be created and accessed."""
    data_list = [
        {'x': torch.tensor([1.0]), 'y': torch.tensor([0.5])}
        for _ in range(5)
    ]
    dataset = GraphDataset(data_list)
    
    assert len(dataset) == 5
    assert dataset.len() == 5
    
    item = dataset.get(0)
    assert item['x'].item() == 1.0

def test_set_seed_reproducibility():
    """Test that set_seed sets random states correctly."""
    set_seed(123)
    r1 = np.random.random()
    
    set_seed(123)
    r2 = np.random.random()
    
    assert r1 == r2