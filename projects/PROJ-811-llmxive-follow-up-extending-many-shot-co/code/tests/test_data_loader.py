import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.data_loader import (
    load_dag_sft_dataset,
    get_dataset_info,
    save_dataset_to_parquet,
    load_dataset_from_parquet
)

@pytest.fixture
def mock_dataset():
    """Mock a HuggingFace dataset."""
    mock_ds = MagicMock()
    mock_ds.features = {"text": "string", "label": "int"}
    mock_ds.num_rows = 100
    mock_ds.__iter__ = lambda self: iter([{"text": "test", "label": 1}] * 100)
    mock_ds.to_parquet = MagicMock()
    return mock_ds

@patch('code.src.data_loader.load_dataset')
def test_load_dag_sft_dataset_success(mock_load, mock_dataset):
    mock_load.return_value = mock_dataset
    ds = load_dag_sft_dataset(split="train")
    mock_load.assert_called_once()
    assert ds == mock_dataset

@patch('code.src.data_loader.load_dataset')
def test_load_dag_sft_dataset_streaming(mock_load, mock_dataset):
    mock_load.return_value = mock_dataset
    ds = load_dag_sft_dataset(split="train", streaming=True)
    mock_load.assert_called_once_with(
        "aaabiao/DAG_sft",
        split="train",
        streaming=True,
        cache_dir=None
    )
    assert ds == mock_dataset

def test_get_dataset_info(mock_dataset):
    info = get_dataset_info(mock_dataset)
    assert info["num_rows"] == 100
    assert "features" in info

@patch('code.src.data_loader.pd')
@patch('code.src.data_loader.Path')
def test_save_dataset_to_parquet(mock_path, mock_pd, mock_dataset):
    mock_file = MagicMock()
    mock_file.is_dir.return_value = False
    mock_path.return_value = mock_file
    
    mock_df = MagicMock()
    mock_pd.DataFrame.return_value = mock_df
    
    result = save_dataset_to_parquet(mock_dataset, "output/test.parquet", "train")
    
    mock_pd.DataFrame.assert_called()
    mock_df.to_parquet.assert_called()
    assert isinstance(result, Path)

@patch('code.src.data_loader.pd')
def test_load_dataset_from_parquet(mock_pd):
    mock_df = MagicMock()
    mock_pd.read_parquet.return_value = mock_df
    
    mock_ds = MagicMock()
    from datasets import Dataset
    with patch.object(Dataset, 'from_pandas', return_value=mock_ds) as mock_from_pandas:
        result = load_dataset_from_parquet("input/test.parquet")
        mock_pd.read_parquet.assert_called_once()
        mock_from_pandas.assert_called_once()
        assert result == mock_ds

def test_load_dag_sft_dataset_failure():
    with patch('code.src.data_loader.load_dataset') as mock_load:
        mock_load.side_effect = Exception("Connection error")
        with pytest.raises(RuntimeError):
            load_dag_sft_dataset(split="train")
