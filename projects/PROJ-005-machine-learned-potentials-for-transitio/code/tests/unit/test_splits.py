"""
tests/unit/test_splits.py
Unit tests for the 5-Fold LLSO logic in src/data/splits.py.
"""
import pytest
import json
import tempfile
from pathlib import Path
from src.data.splits import generate_llso_splits, compute_scaffold_clusters, save_splits_to_json

@pytest.fixture
def mock_data():
    """
    Create mock data with known ligand scaffolds for testing LLSO logic.
    We create 10 samples with 4 distinct scaffolds.
    """
    data = []
    # Scaffold A: samples 0, 1
    data.append({"ligand_scaffold_id": "A", "sample_id": 0})
    data.append({"ligand_scaffold_id": "A", "sample_id": 1})
    # Scaffold B: samples 2, 3
    data.append({"ligand_scaffold_id": "B", "sample_id": 2})
    data.append({"ligand_scaffold_id": "B", "sample_id": 3})
    # Scaffold C: samples 4, 5, 6
    data.append({"ligand_scaffold_id": "C", "sample_id": 4})
    data.append({"ligand_scaffold_id": "C", "sample_id": 5})
    data.append({"ligand_scaffold_id": "C", "sample_id": 6})
    # Scaffold D: samples 7, 8, 9
    data.append({"ligand_scaffold_id": "D", "sample_id": 7})
    data.append({"ligand_scaffold_id": "D", "sample_id": 8})
    data.append({"ligand_scaffold_id": "D", "sample_id": 9})
    return data

def test_compute_scaffold_clusters(mock_data):
    clusters = compute_scaffold_clusters(mock_data)
    assert "A" in clusters
    assert "B" in clusters
    assert "C" in clusters
    assert "D" in clusters
    assert clusters["A"] == [0, 1]
    assert clusters["C"] == [4, 5, 6]

def test_generate_llso_splits_no_leakage(mock_data):
    """
    Test that no scaffold appears in both train and test sets within a fold.
    """
    splits = generate_llso_splits(mock_data, n_folds=2, random_seed=42)
    
    assert len(splits) == 2
    
    for split in splits:
        train_scaffolds = set(split["train_scaffolds"])
        test_scaffolds = set(split["test_scaffolds"])
        
        # Intersection should be empty
        assert len(train_scaffolds.intersection(test_scaffolds)) == 0
        
        # Union should be all scaffolds
        all_scaffolds = {"A", "B", "C", "D"}
        assert train_scaffolds.union(test_scaffolds) == all_scaffolds

def test_generate_llso_splits_insufficient_scaffolds(mock_data):
    """
    Test that an error is raised if n_folds > number of unique scaffolds.
    """
    # We have 4 scaffolds. Requesting 5 folds should fail.
    with pytest.raises(ValueError) as excinfo:
        generate_llso_splits(mock_data, n_folds=5, random_seed=42)
    assert "Cannot perform 5-fold LLSO" in str(excinfo.value)

def test_save_splits_to_json(mock_data):
    splits = generate_llso_splits(mock_data, n_folds=2, random_seed=42)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "splits.json"
        saved_path = save_splits_to_json(splits, output_path)
        
        assert saved_path.exists()
        
        with open(saved_path, 'r') as f:
            loaded_splits = json.load(f)
        
        assert len(loaded_splits) == 2
        assert loaded_splits[0]["fold"] == 0
        assert loaded_splits[1]["fold"] == 1