"""
Unit tests for T013: Client partition metadata generation.
"""

import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

import pytest
from unittest.mock import patch, MagicMock

# Import the function to test
from data.generate_partition_metadata import generate_metadata_for_configuration
from data.partition import load_femnist_data, apply_dirichlet_partition


def test_metadata_schema():
    """Test that generated metadata follows the required schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        data_path = output_dir / "dummy.parquet"

        # Create a dummy parquet file
        dummy_data = pd.DataFrame({
            'user_id': ['user1', 'user2', 'user3'],
            'label': [0, 1, 2],
            'pixels': [[1]*784]*3
        })
        dummy_data.to_parquet(data_path)

        # Mock the partitioning to return predictable results
        mock_partitions = {
            'client_0': pd.DataFrame({'label': [0, 0, 1], 'pixels': [[1]*784]*3}),
            'client_1': pd.DataFrame({'label': [1, 2], 'pixels': [[1]*784]*2})
        }

        with patch('data.generate_partition_metadata.apply_dirichlet_partition', return_value=mock_partitions):
            files = generate_metadata_for_configuration(
                data_path=data_path,
                seed=42,
                alpha=0.5,
                output_dir=output_dir
            )

        assert len(files) == 1
        metadata_path = files[0]
        assert metadata_path.exists()

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        assert isinstance(metadata, list)
        assert len(metadata) == 2

        for item in metadata:
            assert 'client_id' in item
            assert 'label_distribution' in item
            assert 'total_samples' in item
            assert isinstance(item['client_id'], str)
            assert isinstance(item['label_distribution'], dict)
            assert isinstance(item['total_samples'], int)
            assert item['total_samples'] == sum(item['label_distribution'].values())


def test_metadata_filename_pattern():
    """Test that files are named according to the pattern partition_femnist_{seed}_{alpha}.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        data_path = output_dir / "dummy.parquet"

        dummy_data = pd.DataFrame({
            'user_id': ['user1'],
            'label': [0],
            'pixels': [[1]*784]
        })
        dummy_data.to_parquet(data_path)

        mock_partitions = {
            'client_0': pd.DataFrame({'label': [0], 'pixels': [[1]*784]})
        }

        with patch('data.generate_partition_metadata.apply_dirichlet_partition', return_value=mock_partitions):
            files = generate_metadata_for_configuration(
                data_path=data_path,
                seed=123,
                alpha=0.1,
                output_dir=output_dir
            )

        assert len(files) == 1
        filename = files[0].name
        assert filename == "partition_femnist_123_0.1.json"


def test_metadata_label_distribution_accuracy():
    """Test that label distribution counts are accurate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        data_path = output_dir / "dummy.parquet"

        # Create data with known label distribution
        labels = [0, 0, 0, 1, 1, 2]
        dummy_data = pd.DataFrame({
            'user_id': [f'user{i}' for i in range(6)],
            'label': labels,
            'pixels': [[1]*784]*6
        })
        dummy_data.to_parquet(data_path)

        mock_partitions = {
            'client_0': pd.DataFrame({'label': [0, 0, 1], 'pixels': [[1]*784]*3}),
            'client_1': pd.DataFrame({'label': [1, 2, 0], 'pixels': [[1]*784]*3})
        }

        with patch('data.generate_partition_metadata.apply_dirichlet_partition', return_value=mock_partitions):
            files = generate_metadata_for_configuration(
                data_path=data_path,
                seed=42,
                alpha=0.5,
                output_dir=output_dir
            )

        with open(files[0], 'r') as f:
            metadata = json.load(f)

        # Check client_0: labels [0, 0, 1] -> {0: 2, 1: 1}
        client_0_meta = next(m for m in metadata if m['client_id'] == 'client_0')
        assert client_0_meta['label_distribution'] == {'0': 2, '1': 1}
        assert client_0_meta['total_samples'] == 3

        # Check client_1: labels [1, 2, 0] -> {0: 1, 1: 1, 2: 1}
        client_1_meta = next(m for m in metadata if m['client_id'] == 'client_1')
        assert client_1_meta['label_distribution'] == {'0': 1, '1': 1, '2': 1}
        assert client_1_meta['total_samples'] == 3
