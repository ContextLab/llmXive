"""
Unit tests for code/data/downloader.py

These tests verify the OpenML dataset fetching logic.
Note: These are unit tests. For integration tests that actually hit the API,
see tests/integration/test_downloader.py (if created) or rely on the fact
that the downloader is tested in the integration suite.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from data.downloader import DatasetMetadata, fetch_datasets


class TestDatasetMetadata:
    """Tests for the DatasetMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating a DatasetMetadata instance."""
        meta = DatasetMetadata(
            dataset_id=123,
            dataset_name="Test Dataset",
            n_rows=100,
            n_features=5,
            target_name="target"
        )
        assert meta.dataset_id == 123
        assert meta.dataset_name == "Test Dataset"
        assert meta.n_rows == 100
        assert meta.n_features == 5
        assert meta.target_name == "target"


class TestFetcher:
    """Tests for the fetch_datasets function."""

    @patch('data.downloader.openml')
    def test_fetch_datasets_success(self, mock_openml):
        """Test successful fetching of datasets."""
        # Mock the OpenML dataset object
        mock_ds = MagicMock()
        mock_ds.id = 42
        mock_ds.name = "Mock Dataset"
        mock_ds.data_frame = pd.DataFrame(np.random.randn(100, 5), columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        mock_ds.target = 'target'

        # Mock the get method
        mock_openml.datasets.get_dataset.return_value = mock_ds

        # Call the function
        datasets = fetch_datasets([42])

        assert len(datasets) == 1
        assert datasets[0].dataset_id == 42
        assert datasets[0].dataset_name == "Mock Dataset"
        assert datasets[0].n_rows == 100
        assert datasets[0].n_features == 5

    @patch('data.downloader.openml')
    def test_fetch_datasets_invalid_shape(self, mock_openml):
        """Test filtering of datasets with insufficient rows/features."""
        mock_ds = MagicMock()
        mock_ds.id = 42
        mock_ds.name = "Small Dataset"
        # Dataset with too few rows
        mock_ds.data_frame = pd.DataFrame(np.random.randn(50, 5), columns=['f1', 'f2', 'f3', 'f4', 'f5'])
        mock_ds.target = 'target'

        mock_openml.datasets.get_dataset.return_value = mock_ds

        # This should raise a warning or filter out the dataset
        # The actual implementation in T014/T018 handles the filtering logic.
        # Here we just ensure the function doesn't crash on bad data
        datasets = fetch_datasets([42], min_rows=100, min_features=3)

        # Depending on implementation, this might return empty list or raise
        # For this unit test, we assume the function filters internally or raises
        # We assert that if it returns something, it meets the criteria
        if datasets:
            assert all(d.n_rows >= 100 for d in datasets), "Filtered datasets must meet min_rows"
            assert all(d.n_features >= 3 for d in datasets), "Filtered datasets must meet min_features"

    @patch('data.downloader.openml')
    def test_fetch_datasets_api_error(self, mock_openml):
        """Test handling of API errors."""
        mock_openml.datasets.get_dataset.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            fetch_datasets([42])

    @patch('data.downloader.openml')
    def test_downloader_fetches_10_datasets(self, mock_openml):
        """
        TDD-First test for T011:
        Asserts len(datasets) == 10 and all(d.n_rows >= 100) and all(d.n_features >= 3).
        """
        # Create 10 valid mock datasets
        mock_datasets = []
        for i in range(10):
            mock_ds = MagicMock()
            mock_ds.id = 1468 + i
            mock_ds.name = f"Dataset {1468 + i}"
            # Ensure n_rows >= 100 and n_features >= 3
            mock_ds.data_frame = pd.DataFrame(
                np.random.randn(150, 5),
                columns=[f'f{j}' for j in range(5)]
            )
            mock_ds.target = 'target'
            mock_datasets.append(mock_ds)

        # Configure the mock to return these datasets sequentially or by ID
        # Since fetch_datasets likely iterates over IDs, we mock the get call
        def get_dataset_side_effect(dataset_id):
            idx = dataset_id - 1468
            if 0 <= idx < 10:
                return mock_datasets[idx]
            raise ValueError(f"Unexpected dataset ID: {dataset_id}")

        mock_openml.datasets.get_dataset.side_effect = get_dataset_side_effect

        # Call the function with the specific 10 IDs from config.py
        dataset_ids = [1468, 1469, 1470, 1471, 1472, 1473, 1474, 1475, 1476, 1477]
        datasets = fetch_datasets(dataset_ids)

        # Assert the core requirements of T011
        assert len(datasets) == 10, f"Expected 10 datasets, got {len(datasets)}"
        assert all(d.n_rows >= 100 for d in datasets), "All datasets must have >= 100 rows"
        assert all(d.n_features >= 3 for d in datasets), "All datasets must have >= 3 features"