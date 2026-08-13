"""
Unit tests for the data availability verification script.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.verify_dataset import verify_dataset_existence


@patch('src.data.verify_dataset.load_dataset')
@patch('src.data.verify_dataset.setup_logging')
def test_verify_both_datasets_available(mock_setup_logging, mock_load_dataset):
    """Test when both eBird and Daymet datasets are available."""
    mock_logger = MagicMock()
    mock_setup_logging.return_value = mock_logger

    # Mock eBird dataset
    mock_ebird_ds = MagicMock()
    mock_ebird_ds.__iter__ = MagicMock(return_value=iter([{"species": "TestBird"}]))

    # Mock Daymet dataset
    mock_daymet_ds = MagicMock()
    mock_daymet_ds.__iter__ = MagicMock(return_value=iter([{"temp": 20.0}]))

    # Configure load_dataset to return different mocks based on name
    def load_side_effect(name, **kwargs):
        if name == "vvud/eb-data":
            return mock_ebird_ds
        elif name == "daymet/annual":
            return mock_daymet_ds
        raise ValueError(f"Unexpected dataset name: {name}")

    mock_load_dataset.side_effect = load_side_effect

    result = verify_dataset_existence()

    assert result["ebird_available"] is True
    assert result["daymet_available"] is True

    # Check that the report file was written
    # Note: In a real unit test, we might mock the file write as well
    # or use a temporary directory. Here we assume the side effect works.


@patch('src.data.verify_dataset.load_dataset')
@patch('src.data.verify_dataset.setup_logging')
def test_verify_ebird_missing_raises_error(mock_setup_logging, mock_load_dataset):
    """Test that RuntimeError is raised if eBird is missing."""
    mock_logger = MagicMock()
    mock_setup_logging.return_value = mock_logger

    # Mock eBird dataset to fail
    mock_load_dataset.side_effect = Exception("Dataset not found")

    with pytest.raises(RuntimeError, match="eBird dataset"):
        verify_dataset_existence()


@patch('src.data.verify_dataset.load_dataset')
@patch('src.data.verify_dataset.setup_logging')
def test_verify_daymet_missing_does_not_raise(mock_setup_logging, mock_load_dataset):
    """Test that Daymet missing does not raise an error (only eBird is critical)."""
    mock_logger = MagicMock()
    mock_setup_logging.return_value = mock_logger

    # Mock eBird dataset to succeed
    mock_ebird_ds = MagicMock()
    mock_ebird_ds.__iter__ = MagicMock(return_value=iter([{"species": "TestBird"}]))

    # Mock Daymet dataset to fail
    def load_side_effect(name, **kwargs):
        if name == "vvud/eb-data":
            return mock_ebird_ds
        elif name == "daymet/annual":
            raise Exception("Daymet not found")
        raise ValueError(f"Unexpected dataset name: {name}")

    mock_load_dataset.side_effect = load_side_effect

    result = verify_dataset_existence()

    assert result["ebird_available"] is True
    assert result["daymet_available"] is False