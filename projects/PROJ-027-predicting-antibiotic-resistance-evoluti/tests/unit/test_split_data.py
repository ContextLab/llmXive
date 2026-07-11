"""
Unit tests for the split_data module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code_03_model_split_data import load_filtered_matrix, validate_stratification, split_data


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    n_samples = 100
    data = {
        'isolate_id': [f'ISOLATE_{i:03d}' for i in range(n_samples)],
        'resistance_phenotype': np.random.choice(['resistant', 'susceptible'], n_samples, p=[0.3, 0.7]),
        'antibiotic_class': 'beta_lactam',
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_input_file(sample_data):
    """Create a temporary input file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_data.to_csv(f, index=False)
        return Path(f.name)


def test_load_filtered_matrix(temp_input_file):
    """Test loading the filtered matrix."""
    df = load_filtered_matrix(temp_input_file)
    assert len(df) == 100
    assert 'isolate_id' in df.columns
    assert 'resistance_phenotype' in df.columns
    assert 'antibiotic_class' in df.columns


def test_load_filtered_matrix_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_filtered_matrix(Path('/nonexistent/file.csv'))


def test_validate_stratification(sample_data):
    """Test stratification validation."""
    # Should not raise for valid data
    validate_stratification(sample_data, 'resistance_phenotype')


def test_split_data_stratification(sample_data):
    """Test that split maintains stratification."""
    train_df, val_df, test_df = split_data(
        sample_data,
        test_size=0.2,
        val_size=0.1,
        random_state=42
    )

    # Check total size
    assert len(train_df) + len(val_df) + len(test_df) == len(sample_data)

    # Check that proportions are roughly correct (allowing for some variance)
    assert 0.15 < len(train_df) / len(sample_data) < 0.25
    assert 0.08 < len(val_df) / len(sample_data) < 0.12
    assert 0.18 < len(test_df) / len(sample_data) < 0.22

    # Check that all splits have both classes
    for split_df, name in [(train_df, 'train'), (val_df, 'val'), (test_df, 'test')]:
        unique_phenotypes = split_df['resistance_phenotype'].unique()
        assert 'resistant' in unique_phenotypes
        assert 'susceptible' in unique_phenotypes


def test_split_data_reproducibility(sample_data):
    """Test that split is reproducible with same seed."""
    train1, val1, test1 = split_data(sample_data, test_size=0.2, val_size=0.1, random_state=42)
    train2, val2, test2 = split_data(sample_data, test_size=0.2, val_size=0.1, random_state=42)

    # Should be identical
    pd.testing.assert_frame_equal(train1, train2)
    pd.testing.assert_frame_equal(val1, val2)
    pd.testing.assert_frame_equal(test1, test2)


def test_split_data_insufficient_samples():
    """Test handling of insufficient samples for stratification."""
    # Create data with very few samples of one class
    data = {
        'isolate_id': [f'ISOLATE_{i}' for i in range(20)],
        'resistance_phenotype': ['resistant'] * 2 + ['susceptible'] * 18,
        'antibiotic_class': 'beta_lactam',
    }
    df = pd.DataFrame(data)

    # Should still work but may warn
    train_df, val_df, test_df = split_data(df, test_size=0.2, val_size=0.1, random_state=42)
    assert len(train_df) + len(val_df) + len(test_df) == 20