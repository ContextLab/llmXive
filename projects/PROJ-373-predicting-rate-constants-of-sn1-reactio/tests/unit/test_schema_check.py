"""
Unit tests for T011a: schema_check.py
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.schema_check import validate_columns, fetch_dataset_info

class TestValidateColumns:
    def test_all_columns_present(self):
        """Test that validation passes when all required columns are present."""
        dataset_info = {
            "columns": ["smiles", "rate_constant", "substrate_class", "temperature", "solvent"]
        }
        is_valid, missing = validate_columns(dataset_info)
        assert is_valid is True
        assert len(missing) == 0

    def test_missing_one_column(self):
        """Test that validation fails when one required column is missing."""
        dataset_info = {
            "columns": ["smiles", "rate_constant", "substrate_class", "temperature"]
        }
        is_valid, missing = validate_columns(dataset_info)
        assert is_valid is False
        assert "solvent" in missing

    def test_missing_multiple_columns(self):
        """Test that validation fails when multiple required columns are missing."""
        dataset_info = {
            "columns": ["smiles", "rate_constant"]
        }
        is_valid, missing = validate_columns(dataset_info)
        assert is_valid is False
        assert len(missing) == 3
        assert "substrate_class" in missing
        assert "temperature" in missing
        assert "solvent" in missing

    def test_empty_columns(self):
        """Test that validation fails when columns list is empty."""
        dataset_info = {"columns": []}
        is_valid, missing = validate_columns(dataset_info)
        assert is_valid is False
        assert len(missing) == 3

class TestFetchDatasetInfo:
    @patch('data.schema_check.load_dataset')
    def test_fetch_success_with_features(self, mock_load_dataset):
        """Test successful fetch when features are available."""
        mock_ds = MagicMock()
        mock_ds.features = {"smiles": "string", "substrate_class": "string", "temperature": "int", "solvent": "string"}
        mock_load_dataset.return_value = mock_ds

        result = fetch_dataset_info("test_dataset")

        assert result["success"] is True
        assert result["dataset_id"] == "test_dataset"
        assert "substrate_class" in result["columns"]
        assert "temperature" in result["columns"]
        assert "solvent" in result["columns"]

    @patch('data.schema_check.load_dataset')
    def test_fetch_success_with_peek(self, mock_load_dataset):
        """Test successful fetch when features are not available but peek works."""
        mock_ds = MagicMock()
        mock_ds.features = None
        mock_load_dataset.return_value = mock_ds
        
        # Mock the iterator to return a sample item
        mock_item = {"smiles": "C", "substrate_class": "tert", "temperature": 298, "solvent": "water"}
        mock_ds.__iter__ = lambda self: iter([mock_item])

        result = fetch_dataset_info("test_dataset")

        assert result["success"] is True
        assert "substrate_class" in result["columns"]

    @patch('data.schema_check.load_dataset')
    def test_fetch_failure(self, mock_load_dataset):
        """Test fetch failure when dataset is unavailable."""
        mock_load_dataset.side_effect = Exception("Dataset not found")

        result = fetch_dataset_info("invalid_dataset")

        assert result["success"] is False
        assert "error" in result
        assert "Dataset not found" in result["error"]