"""
Integration tests for the split_data module.
Verifies that the stratified split logic correctly divides the data
and that the output files are saved correctly.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from split_data import load_unified_dataset, stratified_split, save_split


@pytest.fixture
def sample_unified_data():
    """
    Creates a sample unified dataset with known nutrient conditions
    to test stratification logic.
    """
    # Create a dataset with 100 rows, ensuring enough samples per class for stratification
    conditions = ['N_high', 'N_low', 'P_high', 'P_low']
    n_samples = 200
    
    data = {
        'accession': [f'Col-0-{i}' for i in range(n_samples)],
        'nutrient_condition': np.random.choice(conditions, n_samples),
        'root_length': np.random.rand(n_samples) * 100,
        'genotype_feature_1': np.random.rand(n_samples),
        'genotype_feature_2': np.random.rand(n_samples)
    }
    
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_stratified_split_distribution(sample_unified_data):
    """
    Test that the stratified split preserves the distribution of nutrient conditions.
    """
    train_df, val_df, test_df = stratified_split(
        sample_unified_data, 
        condition_col='nutrient_condition',
        train_ratio=0.8,
        val_ratio=0.1,
        test_ratio=0.1,
        random_state=42
    )
    
    # Check total count
    assert len(train_df) + len(val_df) + len(test_df) == len(sample_unified_data)
    
    # Check approximate ratios (allowing for some floating point variation)
    assert abs(len(train_df) / len(sample_unified_data) - 0.8) < 0.05
    assert abs(len(val_df) / len(sample_unified_data) - 0.1) < 0.05
    assert abs(len(test_df) / len(sample_unified_data) - 0.1) < 0.05
    
    # Check distribution preservation
    original_dist = sample_unified_data['nutrient_condition'].value_counts(normalize=True)
    train_dist = train_df['nutrient_condition'].value_counts(normalize=True)
    
    # The distribution in the train set should be close to the original
    for cond in original_dist.index:
        diff = abs(original_dist[cond] - train_dist.get(cond, 0))
        assert diff < 0.05, f"Distribution mismatch for {cond}: {original_dist[cond]} vs {train_dist.get(cond, 0)}"


def test_save_split_creates_file(sample_unified_data, temp_output_dir):
    """
    Test that save_split correctly writes a parquet file.
    """
    split_name = "train"
    save_split(sample_unified_data, temp_output_dir, split_name)
    
    expected_path = temp_output_dir / f"{split_name}.parquet"
    assert expected_path.exists(), f"File {expected_path} was not created."
    
    # Verify content
    loaded_df = pd.read_parquet(expected_path)
    assert len(loaded_df) == len(sample_unified_data)
    assert list(loaded_df.columns) == list(sample_unified_data.columns)


def test_load_unified_dataset_fails_on_missing_file(temp_output_dir):
    """
    Test that load_unified_dataset raises FileNotFoundError for missing files.
    """
    missing_path = temp_output_dir / "nonexistent.parquet"
    with pytest.raises(FileNotFoundError):
        load_unified_dataset(missing_path)


def test_full_pipeline_integration(sample_unified_data, temp_output_dir):
    """
    Integration test: Load data, split, save, and reload to verify end-to-end flow.
    """
    # Split
    train_df, val_df, test_df = stratified_split(sample_unified_data, condition_col='nutrient_condition')
    
    # Save
    save_split(train_df, temp_output_dir, "train")
    save_split(val_df, temp_output_dir, "val")
    save_split(test_df, temp_output_dir, "test")
    
    # Reload and verify
    loaded_train = pd.read_parquet(temp_output_dir / "train.parquet")
    loaded_val = pd.read_parquet(temp_output_dir / "val.parquet")
    loaded_test = pd.read_parquet(temp_output_dir / "test.parquet")
    
    assert len(loaded_train) == len(train_df)
    assert len(loaded_val) == len(val_df)
    assert len(loaded_test) == len(test_df)
    
    # Verify no data leakage (rows are unique across splits)
    all_train_ids = set(loaded_train['accession'])
    all_val_ids = set(loaded_val['accession'])
    all_test_ids = set(loaded_test['accession'])
    
    assert len(all_train_ids.intersection(all_val_ids)) == 0
    assert len(all_train_ids.intersection(all_test_ids)) == 0
    assert len(all_val_ids.intersection(all_test_ids)) == 0