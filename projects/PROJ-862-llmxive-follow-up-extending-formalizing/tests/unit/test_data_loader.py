"""
Unit tests for data_loader.py
"""

import pytest
from unittest.mock import patch, MagicMock
from code.data_loader import load_reasoning_dataset, ConfigurationError


def test_load_dataset_missing_columns():
    """Test that ConfigurationError is raised if expected_answer is missing."""
    mock_dataset = MagicMock()
    # Simulate a dataset with wrong columns
    mock_dataset.column_names = ["question", "wrong_column"]
    
    with patch("code.data_loader.load_dataset", return_value=mock_dataset):
        with pytest.raises(ConfigurationError) as excinfo:
            load_reasoning_dataset(
                dataset_name="fake/dataset", 
                subset="test", 
                streaming=False
            )
        assert "missing required columns" in str(excinfo.value)


def test_load_dataset_success():
    """Test successful loading with correct columns."""
    mock_dataset = MagicMock()
    mock_dataset.column_names = ["question", "expected_answer"]
    
    with patch("code.data_loader.load_dataset", return_value=mock_dataset):
        result = load_reasoning_dataset(
            dataset_name="fake/dataset",
            subset="test",
            streaming=False
        )
        assert result == mock_dataset


def test_load_dataset_target_mapping():
    """Test that 'target' column is mapped to 'expected_answer'."""
    mock_dataset = MagicMock()
    mock_dataset.column_names = ["question", "target"]
    mock_dataset.rename_columns.return_value = mock_dataset # Chaining
    mock_dataset.column_names = ["question", "expected_answer"] # After rename
    
    with patch("code.data_loader.load_dataset", return_value=mock_dataset):
        # This should not raise an error and should map the column
        result = load_reasoning_dataset(
            dataset_name="fake/dataset",
            subset="test",
            streaming=False
        )
        # Verify rename was called
        mock_dataset.rename_columns.assert_called_with({"target": "expected_answer"})
