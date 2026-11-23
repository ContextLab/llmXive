"""
Unit tests for the RoboDojo Data Loader.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from src.data_loader import stream_robodojo_tasks, get_dataset_info, load_task_by_id

@pytest.fixture
def mock_dataset():
    """Mock dataset object with streaming capability."""
    ds = MagicMock()
    ds.__iter__ = MagicMock(return_value=iter([{"task_id": "task1", "data": "value1"}, {"task_id": "task2", "data": "value2"}]))
    return ds

@pytest.fixture
def mock_dataset_with_splits():
    """Mock dataset object with multiple splits."""
    ds = MagicMock()
    ds.keys.return_value = ["train", "test"]
    mock_train = MagicMock()
    mock_train.features = {"feature1": "type1"}
    ds.__getitem__ = MagicMock(side_effect=lambda key: mock_train if key == "train" else MagicMock(features={"feature2": "type2"}))
    return ds

def test_stream_robodojo_tasks_streaming():
    """Test that the function streams data correctly."""
    mock_ds = mock_dataset()
    
    with patch('src.data_loader.load_dataset', return_value=mock_ds):
        results = list(stream_robodojo_tasks())
        
    assert len(results) == 2
    assert results[0]["task_id"] == "task1"
    assert results[1]["task_id"] == "task2"

def test_load_task_by_id_found():
    """Test loading a task that exists."""
    mock_ds = mock_dataset()
    
    with patch('src.data_loader.load_dataset', return_value=mock_ds):
        task = load_task_by_id("task1")
        
    assert task is not None
    assert task["task_id"] == "task1"

def test_load_task_by_id_not_found():
    """Test loading a task that does not exist."""
    mock_ds = mock_dataset()
    
    with patch('src.data_loader.load_dataset', return_value=mock_ds):
        task = load_task_by_id("non_existent_task")
        
    assert task is None

def test_get_dataset_info():
    """Test fetching dataset metadata."""
    mock_ds = mock_dataset_with_splits()
    
    with patch('src.data_loader.load_dataset', return_value=mock_ds):
        info = get_dataset_info()
        
    assert "splits" in info
    assert "features" in info
    assert "train" in info["splits"]

def test_stream_robodojo_tasks_raises_on_failure():
    """Test that the function raises RuntimeError if dataset loading fails."""
    with patch('src.data_loader.load_dataset', side_effect=Exception("Connection Error")):
        with pytest.raises(RuntimeError) as excinfo:
            list(stream_robodojo_tasks())
        assert "Failed to load RoboDojo dataset from real source" in str(excinfo.value)

def test_get_dataset_info_raises_on_failure():
    """Test that get_dataset_info raises RuntimeError if fetching fails."""
    with patch('src.data_loader.load_dataset', side_effect=Exception("Connection Error")):
        with pytest.raises(RuntimeError) as excinfo:
            get_dataset_info()
        assert "Failed to fetch dataset info from real source" in str(excinfo.value)