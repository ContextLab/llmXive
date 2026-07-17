import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the project root to the path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.download import download_dataset, download_all_datasets
from src.utils.config import SocraticConfig, set_global_config
import tempfile
import os


@pytest.fixture
def mock_config():
    """Create a temporary config for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = SocraticConfig(
            project_name="test_project",
            data_dir=Path(tmp_dir),
            model_path="test_model",
            seed=42
        )
        set_global_config(config)
        yield config


@patch('src.data.download.load_dataset')
def test_download_dataset_success(mock_load_dataset, mock_config):
    """Test successful download of a dataset."""
    mock_dataset = MagicMock()
    mock_dataset.num_rows = 100
    mock_load_dataset.return_value = mock_dataset

    result = download_dataset("gsm8k", split="train")

    mock_load_dataset.assert_called_once_with("gsm8k", split="train", cache_dir=mock_config.data_dir / "raw" / ".cache", streaming=False)
    assert result is mock_dataset


@patch('src.data.download.load_dataset')
def test_download_dataset_streaming(mock_load_dataset, mock_config):
    """Test downloading with streaming enabled."""
    mock_dataset = MagicMock()
    mock_load_dataset.return_value = mock_dataset

    result = download_dataset("gsm8k", split="train", streaming=True)

    mock_load_dataset.assert_called_once_with("gsm8k", split="train", cache_dir=mock_config.data_dir / "raw" / ".cache", streaming=True)
    assert result is mock_dataset


@patch('src.data.download.load_dataset')
def test_download_dataset_failure(mock_load_dataset, mock_config):
    """Test that download_dataset raises an exception on failure (fail loudly)."""
    mock_load_dataset.side_effect = Exception("Connection failed")

    with pytest.raises(Exception, match="Connection failed"):
        download_dataset("gsm8k", split="train")


@patch('src.data.download.download_dataset')
def test_download_all_datasets(mock_download_dataset, mock_config):
    """Test downloading multiple datasets."""
    mock_ds_gsm = MagicMock()
    mock_ds_math = MagicMock()

    # Configure side effect to return different mocks based on name
    def side_effect(name, **kwargs):
        if name == "gsm8k":
            return mock_ds_gsm
        elif name == "math_dataset":
            return mock_ds_math
        return None

    mock_download_dataset.side_effect = side_effect

    result = download_all_datasets()

    assert "gsm8k" in result
    assert "math_dataset" in result
    assert result["gsm8k"] is mock_ds_gsm
    assert result["math_dataset"] is mock_ds_math

    # Verify calls
    assert mock_download_dataset.call_count == 2
    # Check specific calls
    calls = mock_download_dataset.call_args_list
    assert calls[0][0][0] == "gsm8k"
    assert calls[1][0][0] == "math_dataset"


@patch('src.data.download.download_dataset')
def test_download_all_datasets_failure(mock_download_dataset, mock_config):
    """Test that download_all_datasets fails loudly if one dataset fails."""
    mock_download_dataset.side_effect = Exception("Failed to fetch math")

    with pytest.raises(Exception, match="Failed to fetch math"):
        download_all_datasets()