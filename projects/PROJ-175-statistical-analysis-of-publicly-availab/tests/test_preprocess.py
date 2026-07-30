"""
Tests for preprocessing module.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from code.data.preprocess import (
    build_canonical_map,
    merge_counts,
    compute_marginal_counts,
    normalize_ingredients,
    log_event
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_raw_data(temp_dir):
    """Create sample raw data for testing."""
    data = {
        'recipe_id': [1, 2, 3],
        'ingredients': [
            ['tomato', 'onion', 'garlic'],
            ['tomato', 'onion', 'basil'],
            ['garlic', 'olive oil', 'salt']
        ]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "sample_raw.parquet"
    df.to_parquet(path)
    return path

@pytest.fixture
def sample_marginal_counts(temp_dir):
    """Create sample marginal counts for testing."""
    data = {
        'ingredient_name': ['tomato', 'onion', 'garlic', 'basil', 'olive oil', 'salt'],
        'count': [100, 80, 60, 40, 30, 20]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "marginal_counts.parquet"
    df.to_parquet(path)
    return path

def test_log_event(temp_dir, capsys):
    """Test logging functionality."""
    log_event("TEST", "Test message", {"key": "value"})
    captured = capsys.readouterr()
    assert "Test message" in captured.out
    assert "key" in captured.out

def test_build_canonical_map(temp_dir, sample_marginal_counts):
    """Test building canonical map from marginal counts."""
    canonical_map = build_canonical_map(sample_marginal_counts)
    
    assert isinstance(canonical_map, dict)
    assert len(canonical_map) > 0
    assert 'tomato' in canonical_map
    assert canonical_map['tomato'] == 'tomato'

def test_merge_counts(temp_dir, sample_marginal_counts):
    """Test merging counts based on canonical map."""
    df = pd.read_parquet(sample_marginal_counts)
    canonical_map = build_canonical_map(sample_marginal_counts)
    
    # Create a chunk with some variations
    chunk_data = {
        'ingredient_name': ['tomato', 'tomatoes', 'onion'],
        'count': [50, 30, 20],
        'ingredient_id': [1, 2, 3]
    }
    chunk = pd.DataFrame(chunk_data)
    
    merged = merge_counts(chunk, canonical_map)
    
    assert isinstance(merged, pd.DataFrame)
    assert 'ingredient_name' in merged.columns
    assert 'count' in merged.columns

def test_compute_marginal_counts(temp_dir, sample_raw_data):
    """Test computing marginal counts from raw data."""
    output_path = temp_dir / "output_marginal.parquet"
    
    compute_marginal_counts(sample_raw_data, output_path)
    
    assert output_path.exists()
    
    df = pd.read_parquet(output_path)
    assert 'ingredient_name' in df.columns
    assert 'count' in df.columns
    assert len(df) > 0

def test_normalize_ingredients(temp_dir, sample_raw_data, sample_marginal_counts):
    """Test ingredient normalization."""
    output_normalized = temp_dir / "normalized.parquet"
    output_unique = temp_dir / "unique.parquet"
    report_path = temp_dir / "report.json"
    
    normalize_ingredients(
        raw_data_path=sample_raw_data,
        marginal_counts_path=sample_marginal_counts,
        output_normalized_path=output_normalized,
        output_unique_path=output_unique,
        report_path=report_path
    )
    
    # Check outputs exist
    assert output_normalized.exists()
    assert output_unique.exists()
    assert report_path.exists()
    
    # Check normalized data
    normalized_df = pd.read_parquet(output_normalized)
    assert 'normalized_ingredient' in normalized_df.columns
    assert 'original_ingredient' in normalized_df.columns
    
    # Check unique ingredients
    unique_df = pd.read_parquet(output_unique)
    assert 'ingredient_name' in unique_df.columns
    assert 'ingredient_id' in unique_df.columns
    
    # Check report
    with open(report_path) as f:
        report = json.load(f)
    
    assert report['status'] == 'SUCCESS'
    assert report['normalized_count'] > 0
    assert 'excluded_count' in report
    assert 'timestamp' in report

def test_normalize_with_misspellings(temp_dir):
    """Test normalization handles misspellings correctly."""
    # Create raw data with misspellings
    data = {
        'recipe_id': [1],
        'ingredients': [['tomato', 'onin', 'garlck']]  # Misspellings
    }
    raw_path = temp_dir / "misspelled_raw.parquet"
    pd.DataFrame(data).to_parquet(raw_path)
    
    # Create canonical list with correct spellings
    canonical_data = {
        'ingredient_name': ['tomato', 'onion', 'garlic'],
        'count': [100, 80, 60]
    }
    canonical_path = temp_dir / "canonical.parquet"
    pd.DataFrame(canonical_data).to_parquet(canonical_path)
    
    output_normalized = temp_dir / "normalized.parquet"
    output_unique = temp_dir / "unique.parquet"
    report_path = temp_dir / "report.json"
    
    normalize_ingredients(
        raw_data_path=raw_path,
        marginal_counts_path=canonical_path,
        output_normalized_path=output_normalized,
        output_unique_path=output_unique,
        report_path=report_path
    )
    
    # Verify misspellings were normalized
    normalized_df = pd.read_parquet(output_normalized)
    
    # 'onin' should be normalized to 'onion' (distance 1)
    # 'garlck' should be normalized to 'garlic' (distance 2)
    assert 'onion' in normalized_df['normalized_ingredient'].values
    assert 'garlic' in normalized_df['normalized_ingredient'].values

def test_normalize_excludes_distant_words(temp_dir):
    """Test that words too far from canonical list are excluded."""
    # Create raw data with very different words
    data = {
        'recipe_id': [1],
        'ingredients': ['apple', 'banana', 'xyz123']
    }
    # Convert to proper list format
    data['ingredients'] = [data['ingredients']]
    
    raw_path = temp_dir / "distant_raw.parquet"
    pd.DataFrame(data).to_parquet(raw_path)
    
    # Create canonical list without close matches
    canonical_data = {
        'ingredient_name': ['tomato', 'onion', 'garlic'],
        'count': [100, 80, 60]
    }
    canonical_path = temp_dir / "canonical.parquet"
    pd.DataFrame(canonical_data).to_parquet(canonical_path)
    
    output_normalized = temp_dir / "normalized.parquet"
    output_unique = temp_dir / "unique.parquet"
    report_path = temp_dir / "report.json"
    
    normalize_ingredients(
        raw_data_path=raw_path,
        marginal_counts_path=canonical_path,
        output_normalized_path=output_normalized,
        output_unique_path=output_unique,
        report_path=report_path
    )
    
    # Check report for excluded count
    with open(report_path) as f:
        report = json.load(f)
    
    # 'xyz123' should be excluded (too far from any canonical)
    assert report['excluded_count'] >= 1
    assert report['normalized_count'] == 0  # No matches within threshold
