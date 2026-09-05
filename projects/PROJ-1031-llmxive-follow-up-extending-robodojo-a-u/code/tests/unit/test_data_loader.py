"""
Unit tests for the RoboDojo Data Loader module.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.data_loader import stream_robodojo_tasks, get_dataset_info, load_task_by_id

@pytest.fixture
def mock_dataset():
    """Mock dataset object for testing."""
    mock_ds = MagicMock()
    mock_ds.__iter__ = MagicMock(return_value=iter([
        {"task_id": "task_001", "data": "sample_1"},
        {"task_id": "task_002", "data": "sample_2"},
        {"task_id": "task_003", "data": "sample_3"}
    ]))
    return mock_ds

@pytest.fixture
def mock_dataset_with_splits():
    """Mock dataset object with splits for get_dataset_info."""
    mock_ds = MagicMock()
    mock_ds.keys = MagicMock(return_value=["train", "test"])
    mock_ds.__getitem__ = MagicMock(return_value=MagicMock(features={"feature1": "int"}))
    return mock_ds

def test_stream_robodojo_tasks_streaming(mock_dataset):
    """Test that stream_robodojo_tasks yields items correctly in streaming mode."""
    with patch('src.data_loader.load_dataset', return_value=mock_dataset) as mock_load:
        # Call with streaming=True
        generator = stream_robodojo_tasks(split="train", streaming=True)
        
        # Verify load_dataset was called with correct args
        mock_load.assert_called_once()
        call_args = mock_load.call_args
        assert call_args.kwargs.get('streaming') is True
        assert call_args.kwargs.get('split') == 'train'
        
        # Verify items are yielded
        items = list(generator)
        assert len(items) == 3
        assert items[0]['task_id'] == 'task_001'

def test_load_task_by_id_found(mock_dataset):
    """Test loading a specific task by ID."""
    with patch('src.data_loader.load_dataset', return_value=mock_dataset):
        task = load_task_by_id("task_002")
        assert task is not None
        assert task['task_id'] == 'task_002'

def test_load_task_by_id_not_found(mock_dataset):
    """Test loading a task ID that does not exist."""
    with patch('src.data_loader.load_dataset', return_value=mock_dataset):
        task = load_task_by_id("non_existent_task")
        assert task is None

def test_get_dataset_info(mock_dataset_with_splits):
    """Test retrieving dataset metadata."""
    with patch('src.data_loader.load_dataset', return_value=mock_dataset_with_splits) as mock_load:
        # Call with streaming=False for metadata
        info = get_dataset_info()
        
        mock_load.assert_called_once()
        assert mock_load.call_args.kwargs.get('streaming') is False
        
        assert 'splits' in info
        assert 'train' in info['splits']
        assert 'features' in info

def test_stream_robodojo_tasks_raises_on_failure():
    """Test that stream_robodojo_tasks raises RuntimeError if load_dataset fails."""
    with patch('src.data_loader.load_dataset', side_effect=Exception("Connection Error")):
        with pytest.raises(RuntimeError, match="Failed to load RoboDojo dataset"):
            list(stream_robodojo_tasks())

def test_get_dataset_info_raises_on_failure(mock_dataset):
    """Test that get_dataset_info raises RuntimeError if load_dataset fails."""
    with patch('src.data_loader.load_dataset', side_effect=Exception("Connection Error")):
        with pytest.raises(RuntimeError, match="Failed to fetch dataset info"):
            get_dataset_info()
