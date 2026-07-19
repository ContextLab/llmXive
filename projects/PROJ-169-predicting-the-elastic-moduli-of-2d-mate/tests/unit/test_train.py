"""
Unit tests for the training loop in code/model/train.py.
Tests logic without running full training.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from model.train import (
    GraphDataset,
    filter_graphs_by_split,
    load_split_indices,
    load_graphs_from_parquet,
    collate_fn,
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_graph_dataset_creation():
    """Test that GraphDataset correctly converts dicts to Data objects."""
    graphs = [
        {
            "id": "mp-1",
            "node_features": [[1.0, 2.0], [3.0, 4.0]],
            "edge_index": [[0, 1], [1, 0]],
            "target_moduli": [100.0, 50.0, 0.3],
            "edge_features": [[0.5], [0.5]]
        }
    ]
    dataset = GraphDataset(graphs)
    assert len(dataset) == 1
    
    data_obj = dataset[0]
    assert data_obj.id == "mp-1"
    assert data_obj.x.shape == (2, 2)
    assert data_obj.edge_index.shape == (2, 2)
    assert data_obj.y.shape == (3,)
    assert data_obj.edge_attr.shape == (2, 1)

def test_filter_graphs_by_split():
    """Test filtering graphs by split indices."""
    all_graphs = [
        {"id": "mp-1", "node_features": [], "edge_index": [], "target_moduli": []},
        {"id": "mp-2", "node_features": [], "edge_index": [], "target_moduli": []},
        {"id": "mp-3", "node_features": [], "edge_index": [], "target_moduli": []},
    ]
    split_indices = {
        "train": [{"id": "mp-1"}, {"id": "mp-2"}],
        "test": [{"id": "mp-3"}]
    }
    
    train_graphs = filter_graphs_by_split(all_graphs, split_indices, "train")
    assert len(train_graphs) == 2
    assert {g["id"] for g in train_graphs} == {"mp-1", "mp-2"}
    
    test_graphs = filter_graphs_by_split(all_graphs, split_indices, "test")
    assert len(test_graphs) == 1
    assert test_graphs[0]["id"] == "mp-3"

def test_filter_graphs_missing_split():
    """Test that missing split raises error."""
    split_indices = {"train": []}
    with pytest.raises(ValueError):
        filter_graphs_by_split([], split_indices, "val")

def test_load_split_indices(temp_dir):
    """Test loading split indices from JSON."""
    split_path = Path(temp_dir) / "split.json"
    data = {
        "train": [{"id": "mp-1", "family_id": "F1"}],
        "val": [{"id": "mp-2", "family_id": "F1"}],
        "test": [{"id": "mp-3", "family_id": "F2"}]
    }
    with open(split_path, "w") as f:
        json.dump(data, f)
    
    loaded = load_split_indices(str(split_path))
    assert "train" in loaded
    assert len(loaded["train"]) == 1
    assert loaded["train"][0]["family_id"] == "F1"

def test_load_split_indices_missing_file():
    """Test that missing file raises error."""
    with pytest.raises(FileNotFoundError):
        load_split_indices("nonexistent.json")

def test_collate_fn():
    """Test collate function preserves IDs."""
    from torch_geometric.data import Data
    
    batch = [
        Data(x=np.array([[1.0]]), y=np.array([1.0]), id="mp-1"),
        Data(x=np.array([[2.0]]), y=np.array([2.0]), id="mp-2")
    ]
    _, ids = collate_fn(batch)
    assert ids == ["mp-1", "mp-2"]

@patch("model.train.pd")
def test_load_graphs_from_parquet(mock_pd, temp_dir):
    """Test loading graphs from parquet (mocked)."""
    mock_df = MagicMock()
    mock_df.iterrows.return_value = [
        (0, {"id": "mp-1", "node_features": [[1.0]], "edge_index": [[0,1],[1,0]], "target_moduli": [100.0], "edge_features": [[0.5]]}),
        (1, {"id": "mp-2", "node_features": [[2.0]], "edge_index": [[0,1],[1,0]], "target_moduli": [200.0], "edge_features": [[0.5]]})
    ]
    mock_pd.read_parquet.return_value = mock_df
    
    graphs = load_graphs_from_parquet("dummy.parquet")
    assert len(graphs) == 2
    assert graphs[0]["id"] == "mp-1"
    assert graphs[1]["id"] == "mp-2"