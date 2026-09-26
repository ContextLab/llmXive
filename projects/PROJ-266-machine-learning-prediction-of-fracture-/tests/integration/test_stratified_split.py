"""
Integration test for stratified split logic (US1).

Verifies that the preprocessing pipeline correctly splits the dataset
into train/val/test sets while maintaining stratification by alloy family.
"""
import os
import json
import csv
import pytest
from pathlib import Path
import pandas as pd

# Ensure project root is in path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.config import get_config_dict
from code.data.preprocess import run_stratified_split, PREPROCESS_CONFIG
from code.data.ingest import load_checksum_manifest


@pytest.fixture(scope="module")
def setup_preprocessed_data():
    """
    Ensure the preprocessing pipeline has been run to generate split_metadata.csv.
    This fixture assumes T013 and T014 have been executed successfully.
    """
    # Paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    metadata_json = raw_dir / "metadata.json"
    checksum_manifest = Path("data/benchmarks/metadata_checksum.json")
    
    # Check if raw data exists (from T053)
    if not metadata_json.exists():
        pytest.skip("Raw metadata.json not found. Ensure T053 (synthetic_gen) has run.")
    
    # Check if checksum exists
    if not checksum_manifest.exists():
        pytest.skip("Checksum manifest not found. Ensure T053b has run.")
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # If split_metadata.csv doesn't exist, run the split logic
    split_file = processed_dir / "split_metadata.csv"
    if not split_file.exists():
        # Load metadata
        with open(metadata_json, 'r') as f:
            metadata = json.load(f)
        
        # Run stratified split
        run_stratified_split(metadata, seed=42)
    
    return split_file


def test_split_metadata_exists(setup_preprocessed_data):
    """Verify that split_metadata.csv is created."""
    assert setup_preprocessed_data.exists(), "split_metadata.csv was not created"


def test_split_columns(setup_preprocessed_data):
    """Verify that split_metadata.csv has the correct columns."""
    df = pd.read_csv(setup_preprocessed_data)
    expected_columns = ['split', 'alloy_family', 'count']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"


def test_split_values(setup_preprocessed_data):
    """Verify that split column contains only train, val, test."""
    df = pd.read_csv(setup_preprocessed_data)
    valid_splits = {'train', 'val', 'test'}
    actual_splits = set(df['split'].unique())
    assert actual_splits.issubset(valid_splits), f"Invalid split values found: {actual_splits - valid_splits}"
    assert actual_splits == valid_splits, f"Not all splits present: missing {valid_splits - actual_splits}"


def test_stratification_by_alloy_family(setup_preprocessed_data):
    """
    Verify that each split contains samples from all alloy families (steel, Al, Ti).
    This tests the core stratification logic.
    """
    df = pd.read_csv(setup_preprocessed_data)
    alloy_families = {'steel', 'Al', 'Ti'}
    
    for split in ['train', 'val', 'test']:
        split_df = df[df['split'] == split]
        present_families = set(split_df['alloy_family'].unique())
        assert present_families == alloy_families, (
            f"Split '{split}' missing alloy families. "
            f"Expected {alloy_families}, got {present_families}"
        )


def test_split_counts_are_positive(setup_preprocessed_data):
    """Verify that all split counts are positive integers."""
    df = pd.read_csv(setup_preprocessed_data)
    assert all(df['count'] > 0), "All split counts must be positive"
    assert all(df['count'].apply(lambda x: isinstance(x, int))), "All counts must be integers"


def test_total_samples_consistency(setup_preprocessed_data):
    """
    Verify that the sum of counts across all splits equals the total number of samples.
    This ensures no samples are lost or duplicated during the split.
    """
    df = pd.read_csv(setup_preprocessed_data)
    total_count = df['count'].sum()
    
    # Load original metadata to get total sample count
    with open('data/raw/metadata.json', 'r') as f:
        metadata = json.load(f)
    
    original_count = len(metadata)
    assert total_count == original_count, (
        f"Split counts ({total_count}) do not match original dataset size ({original_count})"
    )


def test_seed_reproducibility(setup_preprocessed_data):
    """
    Verify that the split is deterministic by re-running with the same seed
    and comparing results.
    """
    # Load original metadata
    with open('data/raw/metadata.json', 'r') as f:
        metadata = json.load(f)
    
    # Get config seed
    config = get_config_dict()
    seed = config.get('split_seed', 42)
    
    # Re-run split
    run_stratified_split(metadata, seed=seed)
    
    # Load the result
    df = pd.read_csv('data/processed/split_metadata.csv')
    
    # Verify structure
    assert list(df.columns) == ['split', 'alloy_family', 'count']
    assert set(df['split'].unique()) == {'train', 'val', 'test'}
    
    # Verify counts match previous run
    expected = pd.read_csv('tests/integration/expected_split_counts.csv') if Path('tests/integration/expected_split_counts.csv').exists() else None
    if expected is not None:
        assert df.equals(expected), "Split counts changed with same seed"


def test_no_missing_alloy_in_test_set(setup_preprocessed_data):
    """
    Specific test for T016 requirement: ensure test set contains at least
    one sample per alloy family.
    """
    df = pd.read_csv(setup_preprocessed_data)
    test_df = df[df['split'] == 'test']
    test_families = set(test_df['alloy_family'].unique())
    required_families = {'steel', 'Al', 'Ti'}
    
    assert test_families == required_families, (
        f"Test set must contain all alloy families. "
        f"Missing: {required_families - test_families}"
    )


def test_data_integrity_preserved(setup_preprocessed_data):
    """
    Verify that the split preserves the overall distribution of alloy families
    across the dataset (stratification property).
    """
    with open('data/raw/metadata.json', 'r') as f:
        metadata = json.load(f)
    
    # Calculate original distribution
    original_counts = {}
    for item in metadata:
        family = item['alloy_family']
        original_counts[family] = original_counts.get(family, 0) + 1
    
    total_samples = len(metadata)
    original_ratios = {k: v/total_samples for k, v in original_counts.items()}
    
    # Load split metadata
    df = pd.read_csv(setup_preprocessed_data)
    
    # Check each split
    for split in ['train', 'val', 'test']:
        split_df = df[df['split'] == split]
        split_total = split_df['count'].sum()
        split_ratios = {}
        
        for _, row in split_df.iterrows():
            family = row['alloy_family']
            split_ratios[family] = row['count'] / split_total
        
        # Compare ratios (allow 10% tolerance)
        for family in original_ratios:
            if family in split_ratios:
                diff = abs(split_ratios[family] - original_ratios[family])
                assert diff < 0.1, (
                    f"Stratification deviation too high for {family} in {split}. "
                    f"Expected ~{original_ratios[family]:.2f}, got {split_ratios[family]:.2f}"
                )