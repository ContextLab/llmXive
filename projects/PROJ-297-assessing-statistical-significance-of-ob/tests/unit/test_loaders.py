import pytest
import os
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import functions to test
from loaders import (
    compute_file_hash,
    load_checksums,
    save_checksums,
    detect_constant_variables,
    filter_continuous_variables,
    drop_missing_values,
    apply_hygiene_pipeline
)
from config import get_config

def test_detect_constant_variables():
    df = pd.DataFrame({
        'A': [1, 1, 1],
        'B': [1, 2, 3],
        'C': [5, 5, 5]
    })
    constants = detect_constant_variables(df)
    assert 'A' in constants
    assert 'C' in constants
    assert 'B' not in constants

def test_filter_continuous_variables():
    df = pd.DataFrame({
        'A': [1.0, 2.0, 3.0],
        'B': ['x', 'y', 'z'],
        'C': [1, 2, 3]
    })
    filtered = filter_continuous_variables(df)
    assert list(filtered.columns) == ['A', 'C']
    assert len(filtered.columns) == 2

def test_drop_missing_values():
    df = pd.DataFrame({
        'A': [1.0, 2.0, None],
        'B': [1.0, None, 3.0]
    })
    cleaned = drop_missing_values(df)
    assert len(cleaned) == 0

def test_apply_hygiene_pipeline():
    df = pd.DataFrame({
        'A': [1.0, 2.0, None],
        'B': [1.0, 2.0, 3.0],
        'C': ['x', 'y', 'z'],
        'D': [5.0, 5.0, 5.0]
    })
    cleaned = apply_hygiene_pipeline(df, min_vars=1)
    assert cleaned is not None
    assert 'A' not in cleaned.columns
    assert 'C' not in cleaned.columns
    assert 'D' not in cleaned.columns
    assert 'B' in cleaned.columns

def test_checksum_save_load(tmp_path):
    checksum_file = tmp_path / "checksums.json"
    data = {"file1.csv": "hash123"}
    save_checksums(data, str(checksum_file))
    assert checksum_file.exists()
    loaded = load_checksums(str(checksum_file))
    assert loaded == data

def test_compute_file_hash(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    h = compute_file_hash(str(file_path))
    assert len(h) == 64 # SHA256 hex length

def test_air_quality_url_config():
    """Verify that Air Quality URL is set to direct CSV or handled correctly."""
    config = get_config()
    urls = config.get('dataset_urls', {})
    air_url = urls.get('air_quality')
    assert air_url is not None
    # The task T069 requires using a direct CSV link or verified raw link.
    # We check that it is not a generic placeholder.
    assert 'air-quality' in air_url.lower() or 'airquality' in air_url.lower()