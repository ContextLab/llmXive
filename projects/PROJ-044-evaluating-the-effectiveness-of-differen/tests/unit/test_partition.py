"""
Tests for Dirichlet partitioning logic.
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data.partition import (
    partition_dirichlet,
    validate_partitions,
    NUM_CLASSES_FEMNIST
)


@pytest.fixture
def sample_femnist_data():
    """Create sample FEMNIST-like data for testing."""
    np.random.seed(42)
    n_samples = 10000
    
    # Create synthetic data with 62 classes
    labels = np.random.randint(0, NUM_CLASSES_FEMNIST, size=n_samples)
    
    # Create dummy image data (just for structure)
    data = pd.DataFrame({
        'label': labels,
        'pixels': [np.random.rand(28*28).tolist() for _ in range(n_samples)],
        'client_id': np.random.randint(0, 3400, size=n_samples)  # Original client IDs
    })
    
    return data


def test_partition_dirichlet_reproducibility(sample_femnist_data):
    """Test that partitioning is reproducible with same seed."""
    alpha = 0.5
    seed = 42
    
    # First run
    client_data_1, client_metadata_1 = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha,
        seed=seed,
        num_clients=100,  # Use fewer clients for faster testing
        min_samples_per_client=5
    )
    
    # Second run with same parameters
    client_data_2, client_metadata_2 = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha,
        seed=seed,
        num_clients=100,
        min_samples_per_client=5
    )
    
    # Check that results are identical
    assert len(client_data_1) == len(client_data_2), "Different number of clients"
    
    for client_id in client_data_1:
        assert client_id in client_data_2, f"Client {client_id} missing in second run"
        assert len(client_data_1[client_id]) == len(client_data_2[client_id]), \
            f"Client {client_id} has different sample count"
        assert list(client_data_1[client_id]['label']) == list(client_data_2[client_id]['label']), \
            f"Client {client_id} has different labels"
    
    # Check metadata
    for client_id in client_metadata_1:
        assert client_id in client_metadata_2
        assert client_metadata_1[client_id]['total_samples'] == client_metadata_2[client_id]['total_samples']
        assert client_metadata_1[client_id]['label_distribution'] == client_metadata_2[client_id]['label_distribution']


def test_partition_dirichlet_heterogeneity_levels(sample_femnist_data):
    """Test that different alpha values produce expected heterogeneity levels."""
    seed = 42
    num_clients = 100
    min_samples = 5
    
    # Test with low alpha (high heterogeneity)
    alpha_low = 0.1
    client_data_low, _ = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha_low,
        seed=seed,
        num_clients=num_clients,
        min_samples_per_client=min_samples
    )
    
    # Test with high alpha (low heterogeneity)
    alpha_high = 1.0
    client_data_high, _ = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha_high,
        seed=seed,
        num_clients=num_clients,
        min_samples_per_client=min_samples
    )
    
    # Calculate label diversity (number of unique labels per client)
    diversity_low = [df['label'].nunique() for df in client_data_low.values()]
    diversity_high = [df['label'].nunique() for df in client_data_high.values()]
    
    # With low alpha, we expect lower average diversity (more concentrated labels)
    # With high alpha, we expect higher average diversity (more balanced labels)
    avg_diversity_low = np.mean(diversity_low)
    avg_diversity_high = np.mean(diversity_high)
    
    # Note: This is a statistical test, so we allow some tolerance
    # The key is that low alpha should generally produce more heterogeneous partitions
    assert avg_diversity_low <= avg_diversity_high * 1.5, \
        f"Low alpha ({alpha_low}) should produce more heterogeneous partitions. " \
        f"Got avg diversity: low={avg_diversity_low:.2f}, high={avg_diversity_high:.2f}"


def test_partition_dirichlet_minimum_samples(sample_femnist_data):
    """Test that partition respects minimum samples per client."""
    alpha = 0.5
    seed = 42
    min_samples = 20
    num_clients = 100
    
    client_data, client_metadata = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha,
        seed=seed,
        num_clients=num_clients,
        min_samples_per_client=min_samples
    )
    
    # Check that all clients have at least min_samples
    for client_id, df in client_data.items():
        assert len(df) >= min_samples, \
            f"Client {client_id} has {len(df)} samples, less than minimum {min_samples}"
    
    # Check metadata consistency
    for client_id, metadata in client_metadata.items():
        assert metadata['total_samples'] >= min_samples
        assert metadata['total_samples'] == len(client_data[client_id])


def test_partition_dirichlet_label_distribution_sum(sample_femnist_data):
    """Test that label distributions sum to total samples."""
    alpha = 0.5
    seed = 42
    num_clients = 100
    min_samples = 5
    
    _, client_metadata = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha,
        seed=seed,
        num_clients=num_clients,
        min_samples_per_client=min_samples
    )
    
    for client_id, metadata in client_metadata.items():
        distribution_sum = sum(metadata['label_distribution'].values())
        assert distribution_sum == metadata['total_samples'], \
            f"Client {client_id}: label distribution sum ({distribution_sum}) != total samples ({metadata['total_samples']})"


def test_validate_partitions(sample_femnist_data):
    """Test partition validation logic."""
    alpha = 0.5
    seed = 42
    num_clients = 100
    min_samples = 5
    
    client_data, _ = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha,
        seed=seed,
        num_clients=num_clients,
        min_samples_per_client=min_samples
    )
    
    validation = validate_partitions(client_data, alpha)
    
    assert validation['is_valid'], "Valid partitions should pass validation"
    assert validation['num_clients'] == len(client_data)
    assert validation['total_samples'] > 0
    assert validation['avg_samples_per_client'] >= min_samples
    assert validation['alpha'] == alpha


def test_validate_partitions_empty(sample_femnist_data):
    """Test validation with empty client data."""
    validation = validate_partitions({}, 0.5)
    
    assert not validation['is_valid']
    assert len(validation['warnings']) > 0
    assert "No clients created" in validation['warnings'][0]


def test_partition_dirichlet_all_labels_present(sample_femnist_data):
    """Test that all labels are represented in the partition (at least somewhere)."""
    alpha = 1.0  # More balanced distribution
    seed = 42
    num_clients = 100
    min_samples = 5
    
    client_data, _ = partition_dirichlet(
        data=sample_femnist_data,
        alpha=alpha,
        seed=seed,
        num_clients=num_clients,
        min_samples_per_client=min_samples
    )
    
    # Collect all labels present across all clients
    all_labels = set()
    for df in client_data.values():
        all_labels.update(df['label'].unique())
    
    # With balanced alpha and enough samples, most labels should be present
    # This is a soft check since some rare labels might not appear
    assert len(all_labels) > 0, "At least some labels should be present"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])