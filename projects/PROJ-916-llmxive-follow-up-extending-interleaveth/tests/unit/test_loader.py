"""
Unit tests for src/benchmarks/loader.py
"""
import pytest
from unittest.mock import patch, MagicMock
from datasets import Dataset

from src.benchmarks.loader import (
    load_wise_streaming,
    load_rise_streaming,
    load_benchmark_data,
    WISE_DATASET_ID,
    RISE_DATASET_ID
)
from src.data_models import SceneGraph

def test_wise_mapping():
    """Test that WISE rows are correctly mapped to SceneGraph objects."""
    mock_row = {
        "id": "test-1",
        "objects": [
            {"id": "obj1", "name": "cat", "attributes": ["black"]},
            {"id": "obj2", "name": "mat", "attributes": ["red"]}
        ],
        "relationships": [
            {"subject": "obj1", "predicate": "on", "object": "obj2"}
        ]
    }

    # We need to import the internal mapping function or mock the dataset
    # Since it's not exported, we test via the iterator
    mock_dataset = [mock_row]

    with patch("src.benchmarks.loader.load_dataset") as mock_load:
        mock_load.return_value = mock_dataset

        graphs = list(load_wise_streaming(split="test"))
        assert len(graphs) == 1
        graph = graphs[0]
        assert graph.id == "test-1"
        assert len(graph.objects) == 2
        assert graph.objects[0].name == "cat"
        assert len(graph.relationships) == 1
        assert graph.relationships[0].predicate == "on"

def test_rise_mapping():
    """Test that RISE rows are correctly mapped to SceneGraph objects."""
    mock_row = {
        "id": "rise-1",
        "entities": [
            {"id": "e1", "name": "dog"},
            {"id": "e2", "name": "ball"}
        ],
        "relations": [
            {"head": "e1", "tail": "e2", "type": "chasing"}
        ]
    }

    mock_dataset = [mock_row]

    with patch("src.benchmarks.loader.load_dataset") as mock_load:
        mock_load.return_value = mock_dataset

        graphs = list(load_rise_streaming(split="test"))
        assert len(graphs) == 1
        graph = graphs[0]
        assert graph.source == "RISE"
        assert len(graph.objects) == 2
        assert len(graph.relationships) == 1

def test_wise_failure_raises_file_not_found():
    """Test that missing WISE dataset raises FileNotFoundError."""
    with patch("src.benchmarks.loader.load_dataset") as mock_load:
        mock_load.side_effect = Exception("Dataset not found: wise-scene-graphs")

        with pytest.raises(FileNotFoundError, match="WISE dataset"):
            list(load_wise_streaming())

def test_rise_failure_raises_file_not_found():
    """Test that missing RISE dataset raises FileNotFoundError."""
    with patch("src.benchmarks.loader.load_dataset") as mock_load:
        mock_load.side_effect = Exception("Dataset not found: rise-scene-graphs")

        with pytest.raises(FileNotFoundError, match="RISE dataset"):
            list(load_rise_streaming())

def test_load_benchmark_data_combined():
    """Test loading both datasets."""
    mock_wise = [{"id": "w1", "objects": [], "relationships": []}]
    mock_rise = [{"id": "r1", "entities": [], "relations": []}]

    def side_effect(name, **kwargs):
        if name == WISE_DATASET_ID:
            return mock_wise
        elif name == RISE_DATASET_ID:
            return mock_rise
        return []

    with patch("src.benchmarks.loader.load_dataset", side_effect=side_effect):
        graphs = list(load_benchmark_data(include_wise=True, include_rise=True))
        assert len(graphs) == 2
        sources = [g.source for g in graphs]
        assert "WISE" in sources
        assert "RISE" in sources

def test_load_benchmark_data_empty():
    """Test loading with no datasets."""
    with patch("src.benchmarks.loader.load_dataset") as mock_load:
        graphs = list(load_benchmark_data(include_wise=False, include_rise=False))
        assert len(graphs) == 0
        mock_load.assert_not_called()