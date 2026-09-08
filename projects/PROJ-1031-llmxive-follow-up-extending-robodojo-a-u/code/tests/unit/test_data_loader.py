"""
Unit tests for the RoboDojo data loader module.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.data_loader import stream_robodojo_tasks, get_dataset_info, load_task_by_id

@pytest.fixture
def mock_dataset():
    """Mock dataset iterator returning sample tasks."""
    data = [
        {"task_id": "task_001", "data": "sample_1"},
        {"task_id": "task_002", "data": "sample_2"},
        {"id": "task_003", "data": "sample_3"},
    ]
    mock_ds = MagicMock()
    mock_ds.__iter__ = MagicMock(return_value=iter(data))
    return mock_ds

@pytest.fixture
def mock_dataset_with_splits():
    """Mock dataset with multiple splits."""
    train_data = [{"task_id": f"train_{i}", "data": i} for i in range(3)]
    test_data = [{"task_id": f"test_{i}", "data": i} for i in range(2)]
    
    mock_train = MagicMock()
    mock_train.__iter__ = MagicMock(return_value=iter(train_data))
    
    mock_test = MagicMock()
    mock_test.__iter__ = MagicMock(return_value=iter(test_data))
    
    mock_ds = MagicMock()
    mock_ds.keys = MagicMock(return_value=["train", "test"])
    mock_ds.__getitem__ = MagicMock(side_effect=lambda key: mock_train if key == "train" else mock_test)
    return mock_ds

def test_stream_robodojo_tasks_streaming():
    """Test that stream_robodojo_tasks yields items correctly."""
    mock_data = [
        {"task_id": "t1", "content": "a"},
        {"task_id": "t2", "content": "b"}
    ]
    
    with patch('src.data_loader.load_dataset') as mock_load:
        mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_data))
        
        results = list(stream_robodojo_tasks(streaming=True))
        
        assert len(results) == 2
        assert results[0]["task_id"] == "t1"
        assert results[1]["content"] == "b"
        mock_load.assert_called_once()

def test_load_task_by_id_found():
    """Test loading a task that exists in the stream."""
    mock_data = [
        {"task_id": "target", "val": 1},
        {"task_id": "other", "val": 2}
    ]
    
    with patch('src.data_loader.load_dataset') as mock_load:
        mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_data))
        
        result = load_task_by_id("target")
        
        assert result is not None
        assert result["val"] == 1

def test_load_task_by_id_not_found():
    """Test loading a task that does not exist."""
    mock_data = [{"task_id": "other", "val": 2}]
    
    with patch('src.data_loader.load_dataset') as mock_load:
        mock_load.return_value.__iter__ = MagicMock(return_value=iter(mock_data))
        
        result = load_task_by_id("missing")
        
        assert result is None

def test_get_dataset_info():
    """Test retrieving dataset metadata."""
    mock_features = {"field1": "int", "field2": "string"}
    mock_ds = MagicMock()
    mock_ds.features = mock_features
    mock_ds.keys = MagicMock(return_value=["train"])
    
    with patch('src.data_loader.load_dataset') as mock_load:
        mock_load.return_value = mock_ds
        
        info = get_dataset_info()
        
        assert "features" in info
        assert info["features"] == mock_features

def test_stream_robodojo_tasks_raises_on_failure():
    """Test that streaming raises RuntimeError if dataset load fails."""
    with patch('src.data_loader.load_dataset', side_effect=Exception("Network Error")):
        with pytest.raises(RuntimeError, match="Failed to load RoboDojo dataset"):
            list(stream_robodojo_tasks())

def test_get_dataset_info_raises_on_failure():
    """Test that get_dataset_info raises RuntimeError if fetch fails."""
    with patch('src.data_loader.load_dataset', side_effect=Exception("Network Error")):
        with pytest.raises(RuntimeError, match="Failed to fetch dataset info"):
            get_dataset_info()
