"""
Unit tests for sparsity_generation module.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

from sparsity_generation import (
    load_rss_config,
    load_rss_pool,
    load_test_indices,
    generate_stratified_sample,
    validate_stratification,
    save_subset
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_csv(temp_dir):
    """Create a sample CSV file."""
    path = os.path.join(temp_dir, "test_data.csv")
    df = pd.DataFrame({
        'material_id': [f'mat_{i}' for i in range(100)],
        'formation_energy': np.random.randn(100),
        'composition': ['Fe' for _ in range(100)],
        'dft_computed': [True for _ in range(100)]
    })
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_indices(temp_dir):
    """Create a sample indices file."""
    path = os.path.join(temp_dir, "test_indices.csv")
    indices = pd.DataFrame({'index': list(range(10, 20))})
    indices.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample config file."""
    path = os.path.join(temp_dir, "config.json")
    with open(path, 'w') as f:
        json.dump({'rss_size': 50}, f)
    return path


def test_load_rss_config(sample_config):
    size = load_rss_config(sample_config)
    assert size == 50


def test_load_rss_pool(sample_csv):
    df = load_rss_pool(sample_csv)
    assert len(df) == 100
    assert 'formation_energy' in df.columns


def test_load_test_indices(sample_indices):
    indices = load_test_indices(sample_indices)
    assert len(indices) == 10
    assert 10 in indices
    assert 15 in indices


def test_generate_stratified_sample(sample_csv):
    df = pd.read_csv(sample_csv)
    sample = generate_stratified_sample(df, sample_size=20, random_state=42)
    assert len(sample) == 20
    # Check that the sample is a subset of the original
    assert set(sample['material_id']).issubset(set(df['material_id']))


def test_validate_stratification(sample_csv):
    df = pd.read_csv(sample_csv)
    sample = generate_stratified_sample(df, sample_size=20, random_state=42)
    report = validate_stratification(df, sample, 'formation_energy')
    assert 'ks_statistic' in report
    assert 'p_value' in report
    assert 'is_representative' in report


def test_save_subset(temp_dir, sample_csv):
    df = pd.read_csv(sample_csv)
    output_path = os.path.join(temp_dir, "output.csv")
    checksum = save_subset(df, output_path, metadata={'test': True})
    assert os.path.exists(output_path)
    assert os.path.exists(output_path.replace('.csv', '_metadata.json'))
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
