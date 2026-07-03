import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import logging

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from preprocessing.ingestion import ingest_dataset, RealWorldDataset

logger = logging.getLogger(__name__)

class TestDatasetIngestion:
    """
    Contract test for dataset ingestion (handle missing values, output clean DF).
    Validates that the ingestion pipeline correctly handles missing values
    and returns a clean DataFrame as specified in US4.
    """

    @pytest.fixture
    def sample_missing_data(self):
        """Create a sample DataFrame with missing values for testing."""
        data = {
            'feature_1': [1.0, 2.0, np.nan, 4.0, 5.0],
            'feature_2': [10.0, np.nan, 30.0, 40.0, 50.0],
            'target': [0, 1, 0, 1, 0]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_complete_data(self):
        """Create a sample DataFrame without missing values."""
        data = {
            'feature_1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_2': [10.0, 20.0, 30.0, 40.0, 50.0],
            'target': [0, 1, 0, 1, 0]
        }
        return pd.DataFrame(data)

    def test_ingest_dataset_handles_missing_values(self, sample_missing_data, tmp_path):
        """
        Contract: ingest_dataset must handle missing values by imputation.
        Output must be a clean DataFrame with no NaN values.
        """
        # Save sample data to a temporary CSV
        csv_path = tmp_path / "test_missing.csv"
        sample_missing_data.to_csv(csv_path, index=False)

        # Ingest the dataset
        result_df, metadata = ingest_dataset(
            source_path=str(csv_path),
            dataset_id="test_missing_dataset",
            impute_strategy="mean"
        )

        # Verify no missing values remain
        assert not result_df.isnull().any().any(), "Ingested dataset still contains missing values"

        # Verify metadata tracks the imputation
        assert "imputation_count" in metadata, "Metadata should track imputation count"
        assert metadata["imputation_count"] > 0, "Imputation count should be positive when missing values exist"

        # Verify output is a DataFrame
        assert isinstance(result_df, pd.DataFrame), "Output must be a pandas DataFrame"

    def test_ingest_dataset_preserves_complete_data(self, sample_complete_data, tmp_path):
        """
        Contract: ingest_dataset must preserve complete data without modification.
        """
        # Save sample data to a temporary CSV
        csv_path = tmp_path / "test_complete.csv"
        sample_complete_data.to_csv(csv_path, index=False)

        # Ingest the dataset
        result_df, metadata = ingest_dataset(
            source_path=str(csv_path),
            dataset_id="test_complete_dataset",
            impute_strategy="mean"
        )

        # Verify no missing values (should be zero)
        assert not result_df.isnull().any().any(), "Complete dataset should have no missing values"
        assert metadata.get("imputation_count", 0) == 0, "Imputation count should be zero for complete data"

        # Verify data integrity
        pd.testing.assert_frame_equal(result_df, sample_complete_data)

    def test_ingest_dataset_returns_real_world_dataset_entity(self, sample_missing_data, tmp_path):
        """
        Contract: ingest_dataset must return a RealWorldDataset entity with metadata.
        """
        csv_path = tmp_path / "test_entity.csv"
        sample_missing_data.to_csv(csv_path, index=False)

        # Ingest the dataset
        result_df, metadata = ingest_dataset(
            source_path=str(csv_path),
            dataset_id="test_entity_dataset",
            impute_strategy="mean"
        )

        # Verify metadata structure matches RealWorldDataset expectations
        required_fields = ["dataset_id", "source_path", "row_count", "column_count", "missing_rate"]
        for field in required_fields:
            assert field in metadata, f"Metadata must contain {field}"

        assert metadata["dataset_id"] == "test_entity_dataset"
        assert metadata["row_count"] == sample_missing_data.shape[0]
        assert metadata["column_count"] == sample_missing_data.shape[1]
        assert metadata["missing_rate"] > 0, "Missing rate should be positive for data with NaNs"

    def test_ingest_dataset_invalid_file_raises_error(self, tmp_path):
        """
        Contract: ingest_dataset must raise an error for non-existent files.
        """
        non_existent_path = tmp_path / "does_not_exist.csv"

        with pytest.raises(FileNotFoundError):
            ingest_dataset(
                source_path=str(non_existent_path),
                dataset_id="test_invalid",
                impute_strategy="mean"
            )

    def test_ingest_dataset_invalid_format_raises_error(self, tmp_path):
        """
        Contract: ingest_dataset must raise an error for invalid file formats.
        """
        invalid_path = tmp_path / "test_invalid.txt"
        invalid_path.write_text("This is not a CSV file")

        with pytest.raises(Exception):
            ingest_dataset(
                source_path=str(invalid_path),
                dataset_id="test_invalid_format",
                impute_strategy="mean"
            )