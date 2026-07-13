"""
Unit tests for k-fold cross-validation utilities.
"""
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

from code.training.kfold_utils import (
    load_dataset_metadata,
    create_stratification_bins,
    create_combined_stratification,
    stratified_k_fold_split,
    get_fold_sizes
)


@pytest.fixture
def temp_metadata_file():
    """Create a temporary metadata file for testing."""
    temp_dir = tempfile.mkdtemp()
    metadata_path = os.path.join(temp_dir, 'test_metadata.json')

    # Create synthetic metadata
    data = []
    n_samples = 100
    for i in range(n_samples):
        data.append({
            'seed': i,
            'inclusion_density': 0.1 + (i % 10) * 0.05,  # Varying densities
            'clustering_coefficient': 0.2 + (i % 5) * 0.1  # Varying clustering
        })

    with open(metadata_path, 'w') as f:
        json.dump(data, f)

    yield metadata_path

    # Cleanup
    os.remove(metadata_path)
    os.rmdir(temp_dir)


def test_load_dataset_metadata(temp_metadata_file):
    """Test loading dataset metadata."""
    densities, clustering_coeffs = load_dataset_metadata(temp_metadata_file)

    assert len(densities) == 100
    assert len(clustering_coeffs) == 100
    assert isinstance(densities, np.ndarray)
    assert isinstance(clustering_coeffs, np.ndarray)
    assert densities.min() >= 0.1
    assert densities.max() <= 0.55


def test_create_stratification_bins_quantile():
    """Test quantile-based binning."""
    values = np.random.rand(100)
    bins = create_stratification_bins(values, n_bins=5, bin_type='quantile')

    assert len(bins) == 100
    assert bins.min() >= 1
    assert bins.max() <= 5


def test_create_stratification_bins_uniform():
    """Test uniform binning."""
    values = np.linspace(0, 1, 100)
    bins = create_stratification_bins(values, n_bins=5, bin_type='uniform')

    assert len(bins) == 100
    assert bins.min() >= 1
    assert bins.max() <= 5


def test_create_combined_stratification():
    """Test combined stratification label creation."""
    densities = np.random.rand(100)
    clustering_coeffs = np.random.rand(100)

    combined = create_combined_stratification(
        densities, clustering_coeffs,
        n_density_bins=5, n_clustering_bins=5
    )

    assert len(combined) == 100
    # Max possible label should be (5-1)*5 + 5 = 25
    assert combined.max() <= 25


def test_stratified_k_fold_split(temp_metadata_file):
    """Test stratified k-fold split generation."""
    folds = list(stratified_k_fold_split(
        temp_metadata_file,
        n_splits=5,
        n_density_bins=5,
        n_clustering_bins=5
    ))

    assert len(folds) == 5

    # Check that all indices are used exactly once across folds
    all_train_indices = []
    all_test_indices = []
    for train_idx, test_idx in folds:
        all_train_indices.extend(train_idx)
        all_test_indices.extend(test_idx)

    # Each sample should appear in test set exactly once
    assert sorted(all_test_indices) == list(range(100))

    # Check that train and test sets are disjoint for each fold
    for train_idx, test_idx in folds:
        assert len(set(train_idx) & set(test_idx)) == 0


def test_get_fold_sizes(temp_metadata_file):
    """Test fold size calculation."""
    fold_sizes = get_fold_sizes(
        temp_metadata_file,
        n_splits=5,
        n_density_bins=5,
        n_clustering_bins=5
    )

    assert len(fold_sizes) == 5

    total_test_size = sum(f['test_size'] for f in fold_sizes)
    assert total_test_size == 100

    # Check that mean densities are reasonable
    for fold in fold_sizes:
        assert 0 <= fold['train_mean_density'] <= 1
        assert 0 <= fold['test_mean_density'] <= 1


def test_stratified_k_fold_with_small_dataset():
    """Test k-fold split with a very small dataset."""
    temp_dir = tempfile.mkdtemp()
    metadata_path = os.path.join(temp_dir, 'small_metadata.json')

    # Create small metadata (only 10 samples)
    data = []
    for i in range(10):
        data.append({
            'seed': i,
            'inclusion_density': 0.1 + i * 0.05,
            'clustering_coefficient': 0.2 + i * 0.05
        })

    with open(metadata_path, 'w') as f:
        json.dump(data, f)

    try:
        folds = list(stratified_k_fold_split(
            metadata_path,
            n_splits=5,
            n_density_bins=2,
            n_clustering_bins=2
        ))

        assert len(folds) == 5

        # Each fold should have at least some samples
        for train_idx, test_idx in folds:
            assert len(train_idx) > 0
            assert len(test_idx) > 0

    finally:
        os.remove(metadata_path)
        os.rmdir(temp_dir)