import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from code.data_loader import (
    load_manifest, 
    calculate_checksum, 
    validate_dataset, 
    load_datasets
)

def test_validate_dataset_min_rows():
    """Test that datasets with fewer than 50 rows are rejected."""
    df = pd.DataFrame({'a': range(10), 'b': range(10)})
    info = {'name': 'test_small'}
    assert not validate_dataset(df, info)

def test_validate_dataset_has_numeric():
    """Test that datasets with numeric columns pass."""
    df = pd.DataFrame({'a': range(100), 'b': range(100)})
    info = {'name': 'test_numeric'}
    assert validate_dataset(df, info)

def test_validate_dataset_has_categorical():
    """Test that datasets with categorical columns pass."""
    df = pd.DataFrame({'a': ['x'] * 100, 'b': ['y'] * 100})
    info = {'name': 'test_cat'}
    assert validate_dataset(df, info)

def test_validate_dataset_mixed():
    """Test that datasets with both numeric and categorical pass."""
    df = pd.DataFrame({'a': range(100), 'b': ['x'] * 100})
    info = {'name': 'test_mixed'}
    assert validate_dataset(df, info)

def test_calculate_checksum():
    """Test checksum calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"hello world")
        tmp_path = tmp.name
    
    try:
        checksum = calculate_checksum(tmp_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert checksum == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    finally:
        os.unlink(tmp_path)