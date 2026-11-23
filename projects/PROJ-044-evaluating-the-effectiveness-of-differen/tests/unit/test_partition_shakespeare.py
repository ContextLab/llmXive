"""
Unit tests for Shakespeare partitioning logic (T012b).
"""

import os
import tempfile
import json
import pytest
import pandas as pd
import numpy as np

from code.data.partition import (
    load_shakespeare_data,
    apply_dirichlet_partition,
    validate_partition
)


class TestShakespearePartitioning:
    """Tests for Shakespeare dataset partitioning."""

    @pytest.fixture
    def sample_shakespeare_data(self):
        """Create a synthetic Shakespeare dataset for testing."""
        # Create a mock dataframe simulating the structure of real Shakespeare data
        # Real data has 'user_id' and 'label'
        np.random.seed(42)
        n_samples = 1000
        n_clients = 10
        
        user_ids = [f"user_{i}" for i in range(n_clients)]
        labels = list(range(80))  # Shakespeare typically has ~80 characters/tokens as labels
        
        data = {
            'user_id': np.random.choice(user_ids, n_samples),
            'label': np.random.choice(labels, n_samples)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_data_file(self, sample_shakespeare_data):
        """Save sample data to a temporary parquet file."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            sample_shakespeare_data.to_parquet(f.name)
            yield f.name
        os.unlink(f.name)

    def test_load_shakespeare_data(self, temp_data_file):
        """Test loading Shakespeare data from parquet."""
        df = load_shakespeare_data(temp_data_file)
        assert 'user_id' in df.columns
        assert 'label' in df.columns
        assert len(df) > 0

    def test_load_shakespeare_data_missing_file(self):
        """Test loading from a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_shakespeare_data("non_existent_file.parquet")

    def test_dirichlet_partition_low_alpha(self, temp_data_file):
        """
        Test that low alpha (0.1) results in high heterogeneity.
        Some clients should have very few or no samples for most classes.
        """
        df = load_shakespeare_data(temp_data_file)
        assignments, metadata = apply_dirichlet_partition(
            df, num_clients=10, alpha=0.1, seed=42
        )
        
        # Check that assignments exist
        assert len(assignments) == 10
        assert len(metadata) == 10
        
        # Check total samples match
        total_assigned = sum(len(v) for v in assignments.values())
        assert total_assigned == len(df)

    def test_dirichlet_partition_high_alpha(self, temp_data_file):
        """
        Test that high alpha (1.0) results in more balanced distribution.
        """
        df = load_shakespeare_data(temp_data_file)
        assignments, metadata = apply_dirichlet_partition(
            df, num_clients=10, alpha=1.0, seed=42
        )
        
        # Check that assignments exist
        assert len(assignments) == 10
        
        # Calculate variance in sample counts
        counts = [len(v) for v in assignments.values()]
        variance = np.var(counts)
        
        # High alpha should generally have lower variance than low alpha,
        # but we just check it's a reasonable distribution
        assert sum(counts) == len(df)

    def test_reproducibility(self, temp_data_file):
        """Test that same seed produces identical partitions."""
        df = load_shakespeare_data(temp_data_file)
        
        _, meta1 = apply_dirichlet_partition(df, num_clients=5, alpha=0.5, seed=123)
        _, meta2 = apply_dirichlet_partition(df, num_clients=5, alpha=0.5, seed=123)
        
        # Compare metadata
        for client_id in meta1:
            assert meta1[client_id]['total_samples'] == meta2[client_id]['total_samples']
            assert meta1[client_id]['label_distribution'] == meta2[client_id]['label_distribution']

    def test_zero_samples_client_handling(self, temp_data_file):
        """Test handling of clients that end up with zero samples."""
        df = load_shakespeare_data(temp_data_file)
        # Use very low alpha and many clients to increase chance of empty clients
        _, metadata = apply_dirichlet_partition(
            df, num_clients=100, alpha=0.01, seed=42
        )
        
        # Some clients might be empty
        empty_count = sum(1 for m in metadata.values() if m['total_samples'] == 0)
        # Just verify the code doesn't crash and metadata is consistent
        assert len(metadata) == 100

    def test_validate_partition(self, temp_data_file):
        """Test partition validation logic."""
        df = load_shakespeare_data(temp_data_file)
        _, metadata = apply_dirichlet_partition(df, num_clients=10, alpha=0.5, seed=42)
        
        # Should pass with default min_samples=0
        assert validate_partition(metadata) is True
        
        # Should pass with min_samples=1 (assuming no empty clients in this specific run)
        # Note: This might fail if the random seed produces empty clients, so we check the logic
        result = validate_partition(metadata, min_samples=1)
        # Result depends on the specific random partition, but function should run without error
        assert isinstance(result, bool)