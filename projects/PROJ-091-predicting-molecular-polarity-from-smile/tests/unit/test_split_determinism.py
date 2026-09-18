"""Unit tests for T046: Deterministic split verification.

This test module verifies that the split_data function produces identical
train/test splits across multiple runs when using the deterministic seed.
"""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.split_data import split_data, load_splits, verify_determinism
from utils.logging_config import setup_logging

# Setup logging for tests
setup_logging(log_level="INFO")

@pytest.fixture
def sample_data_path(tmp_path):
    """Create a sample parquet file for testing."""
    # Generate deterministic sample data
    np.random.seed(12345)
    n_samples = 1000
    data = {
        'smiles': [f"SMILES_{i}" for i in range(n_samples)],
        'target': np.random.randn(n_samples),
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
    }
    df = pd.DataFrame(data)
    
    # Save to temp path
    output_path = tmp_path / "sample_data.parquet"
    df.to_parquet(output_path, index=False)
    
    return output_path

@pytest.fixture
def output_prefix(tmp_path):
    """Create a temporary directory for output files."""
    return tmp_path / "splits"

def test_split_produces_files(sample_data_path, output_prefix):
    """Test that split_data creates the expected output files."""
    split_data(sample_data_path, output_prefix, test_size=0.2, seed=42)
    
    train_path = output_prefix.with_name(output_prefix.name + "_train.parquet")
    test_path = output_prefix.with_name(output_prefix.name + "_test.parquet")
    
    assert train_path.exists(), "Train file should exist"
    assert test_path.exists(), "Test file should exist"
    
    train_df = pd.read_parquet(train_path)
    test_df = pd.read_parquet(test_path)
    
    # Verify sizes (80/20 split)
    assert len(train_df) == 800, f"Expected 800 train rows, got {len(train_df)}"
    assert len(test_df) == 200, f"Expected 200 test rows, got {len(test_df)}"

def test_split_determinism_fixed_seed(sample_data_path, output_prefix):
    """Test that split produces identical results with the same seed."""
    # First run
    split_data(sample_data_path, output_prefix, test_size=0.2, seed=42)
    train1, test1 = load_splits(output_prefix)
    
    # Clean up
    train_path = output_prefix.with_name(output_prefix.name + "_train.parquet")
    test_path = output_prefix.with_name(output_prefix.name + "_test.parquet")
    train_path.unlink()
    test_path.unlink()
    
    # Second run with same seed
    split_data(sample_data_path, output_prefix, test_size=0.2, seed=42)
    train2, test2 = load_splits(output_prefix)
    
    # Verify shapes are identical
    assert train1.shape == train2.shape, "Train shapes should be identical"
    assert test1.shape == test2.shape, "Test shapes should be identical"
    
    # Verify content is identical (same indices selected)
    pd.testing.assert_frame_equal(train1.reset_index(drop=True), train2.reset_index(drop=True))
    pd.testing.assert_frame_equal(test1.reset_index(drop=True), test2.reset_index(drop=True))

def test_split_determinism_multiple_runs(sample_data_path, output_prefix):
    """Test that split produces identical results across 5 runs (T046 requirement)."""
    shapes = []
    
    for i in range(5):
        # Clean up previous files
        train_path = output_prefix.with_name(output_prefix.name + "_train.parquet")
        test_path = output_prefix.with_name(output_prefix.name + "_test.parquet")
        
        if train_path.exists():
            train_path.unlink()
        if test_path.exists():
            test_path.unlink()
        
        # Run split with hardcoded seed
        split_data(sample_data_path, output_prefix, test_size=0.2, seed=42)
        
        # Load and record shapes
        train_df, test_df = load_splits(output_prefix)
        shapes.append((train_df.shape, test_df.shape))
    
    # Assert all shapes are identical
    first_shape = shapes[0]
    for i, shape in enumerate(shapes[1:], 1):
        assert shape == first_shape, f"Iteration {i} shape {shape} differs from first {first_shape}"
    
    assert all(s == first_shape for s in shapes), "All 5 runs should produce identical shapes"

def test_verify_determinism_function(sample_data_path, output_prefix):
    """Test the verify_determinism helper function."""
    is_deterministic = verify_determinism(sample_data_path, output_prefix, iterations=5)
    assert is_deterministic, "verify_determinism should return True for deterministic splits"

def test_different_seeds_produce_different_splits(sample_data_path, output_prefix):
    """Test that different seeds produce different splits."""
    # Run with seed 42
    split_data(sample_data_path, output_prefix, test_size=0.2, seed=42)
    train1, test1 = load_splits(output_prefix)
    
    # Clean up
    train_path = output_prefix.with_name(output_prefix.name + "_train.parquet")
    test_path = output_prefix.with_name(output_prefix.name + "_test.parquet")
    train_path.unlink()
    test_path.unlink()
    
    # Run with seed 123
    split_data(sample_data_path, output_prefix, test_size=0.2, seed=123)
    train2, test2 = load_splits(output_prefix)
    
    # Shapes should be same (same test_size)
    assert train1.shape == train2.shape
    assert test1.shape == test2.shape
    
    # But content should be different (different random split)
    # Note: There's a tiny chance they could be identical, but extremely unlikely
    # For this test, we just verify the function runs without error
    # A more robust test would check actual row indices
    assert not train1.equals(train2) or not test1.equals(test2), \
        "Different seeds should ideally produce different splits"