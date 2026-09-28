"""
Unit tests for T013: Client Partition Metadata Generation
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from data.generate_partition_metadata import generate_metadata_for_configuration
from data.partition import PartitionError


class TestGenerateMetadata:
    """Test metadata generation logic."""

    @pytest.fixture
    def mock_femnist_data(self):
        """Create mock FEMNIST data for testing."""
        np.random.seed(42)
        n_samples = 1000
        n_clients = 10
        n_classes = 62

        data = {
            'user_id': np.repeat([f'user_{i}' for i in range(n_clients)], n_samples // n_clients),
            'label': np.random.randint(0, n_classes, n_samples)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "partitions"
        output_dir.mkdir()
        return output_dir

    @pytest.fixture
    def temp_data_file(self, tmp_path, mock_femnist_data):
        """Create temporary data file."""
        data_file = tmp_path / "femnist.parquet"
        mock_femnist_data.to_parquet(data_file)
        return data_file

    def test_metadata_generation_femnist(
        self,
        mock_femnist_data,
        temp_data_file,
        temp_output_dir
    ):
        """Test metadata generation for valid FEMNIST configuration."""
        seed = 42
        alpha = 0.1

        with patch('data.generate_partition_metadata.load_femnist_data') as mock_load, \
             patch('data.generate_partition_metadata.apply_dirichlet_partition') as mock_partition, \
             patch('data.generate_partition_metadata.validate_partition') as mock_validate, \
             patch('data.generate_partition_metadata.generate_checksum_file') as mock_checksum:

            # Setup mocks
            mock_load.return_value = mock_femnist_data
            mock_partition.return_value = {
                'user_0': mock_femnist_data.iloc[:100],
                'user_1': mock_femnist_data.iloc[100:200],
            }

            output_path = generate_metadata_for_configuration(
                seed=seed,
                alpha=alpha,
                dataset_name="femnist",
                output_dir=temp_output_dir
            )

            # Verify output file exists
            assert output_path.exists()

            # Verify JSON structure
            with open(output_path, 'r') as f:
                metadata = json.load(f)

            assert isinstance(metadata, list)
            assert len(metadata) > 0

            # Check schema
            for client_meta in metadata:
                assert 'client_id' in client_meta
                assert 'label_distribution' in client_meta
                assert 'total_samples' in client_meta
                assert isinstance(client_meta['client_id'], str)
                assert isinstance(client_meta['label_distribution'], dict)
                assert isinstance(client_meta['total_samples'], int)

    def test_shakespeare_exclusion(self, temp_output_dir):
        """Test that Shakespeare dataset is excluded per T000."""
        with pytest.raises(ValueError) as exc_info:
            generate_metadata_for_configuration(
                seed=42,
                alpha=0.1,
                dataset_name="shakespeare",
                output_dir=temp_output_dir
            )

        assert "T000" in str(exc_info.value)
        assert "Shakespeare" in str(exc_info.value)
        assert "excluded" in str(exc_info.value).lower()

    def test_invalid_alpha_values(self, mock_femnist_data, temp_data_file, temp_output_dir):
        """Test metadata generation with various alpha values."""
        for alpha in [0.1, 0.5, 1.0]:
            with patch('data.generate_partition_metadata.load_femnist_data') as mock_load, \
                 patch('data.generate_partition_metadata.apply_dirichlet_partition') as mock_partition, \
                 patch('data.generate_partition_metadata.validate_partition'), \
                 patch('data.generate_partition_metadata.generate_checksum_file'):

                mock_load.return_value = mock_femnist_data
                mock_partition.return_value = {
                    'user_0': mock_femnist_data.iloc[:50],
                }

                output_path = generate_metadata_for_configuration(
                    seed=42,
                    alpha=alpha,
                    dataset_name="femnist",
                    output_dir=temp_output_dir
                )

                assert output_path.exists()
                assert f"partition_femnist_42_{alpha}.json" in str(output_path)

    def test_metadata_schema_compliance(self, mock_femnist_data, temp_data_file, temp_output_dir):
        """Test that output metadata strictly follows required schema."""
        with patch('data.generate_partition_metadata.load_femnist_data') as mock_load, \
             patch('data.generate_partition_metadata.apply_dirichlet_partition') as mock_partition, \
             patch('data.generate_partition_metadata.validate_partition'), \
             patch('data.generate_partition_metadata.generate_checksum_file'):

            mock_load.return_value = mock_femnist_data
            mock_partition.return_value = {
                'client_123': mock_femnist_data.iloc[:100],
            }

            output_path = generate_metadata_for_configuration(
                seed=123,
                alpha=0.5,
                dataset_name="femnist",
                output_dir=temp_output_dir
            )

            with open(output_path, 'r') as f:
                metadata = json.load(f)

            # Verify exact schema requirements
            assert len(metadata) == 1
            entry = metadata[0]

            # Required keys
            assert set(entry.keys()) == {'client_id', 'label_distribution', 'total_samples'}

            # Type checks
            assert isinstance(entry['client_id'], str)
            assert isinstance(entry['label_distribution'], dict)
            assert isinstance(entry['total_samples'], int)

            # Label distribution format
            for key, value in entry['label_distribution'].items():
                assert isinstance(key, str)  # JSON keys are strings
                assert isinstance(value, int)