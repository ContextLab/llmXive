"""
Integration Test for T068: Multi-Cohort Harmonization

Verifies that:
1. The harmonization script runs without error.
2. The output files are created.
3. The output files have the expected structure.
"""
import os
import sys
import json
import pytest
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from harmonize_data import main, fetch_microbiome_data, fetch_sleep_data, harmonize_datasets


def test_fetch_microbiome_data():
    """Test that microbiome data is fetched correctly."""
    df = fetch_microbiome_data(source_type="synthetic_proxy")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'subject_id' in df.columns
    assert 'age' in df.columns
    assert 'sex' in df.columns
    assert 'bmi' in df.columns
    # Check for taxa columns
    taxa_cols = [c for c in df.columns if c.startswith('taxa_')]
    assert len(taxa_cols) > 0


def test_fetch_sleep_data():
    """Test that sleep data is fetched correctly."""
    df = fetch_sleep_data(source_type="synthetic_proxy")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'subject_id' in df.columns
    assert 'age' in df.columns
    assert 'sex' in df.columns
    assert 'bmi' in df.columns
    assert 'sleep_duration' in df.columns
    assert 'sws_duration' in df.columns


def test_harmonize_datasets():
    """Test the harmonization logic."""
    mb_df = fetch_microbiome_data(source_type="synthetic_proxy")
    sl_df = fetch_sleep_data(source_type="synthetic_proxy")
    
    harmonized_df, meta_log = harmonize_datasets(mb_df, sl_df)
    
    assert isinstance(harmonized_df, pd.DataFrame)
    assert len(harmonized_df) > 0
    assert 'subject_id' in harmonized_df.columns
    
    # Check metadata log
    assert isinstance(meta_log, dict)
    assert 'matching_strategy' in meta_log
    assert 'matched_count' in meta_log
    assert meta_log['matched_count'] > 0


def test_harmonization_output_files():
    """Test that the main function produces the required output files."""
    # Run the main function
    main()
    
    # Check file existence
    parquet_path = Path("data/processed/harmonized_data.parquet")
    json_path = Path("data/metadata/harmonization_metadata.json")
    
    assert parquet_path.exists(), f"Expected file {parquet_path} does not exist."
    assert json_path.exists(), f"Expected file {json_path} does not exist."
    
    # Validate parquet content
    df = pd.read_parquet(parquet_path)
    assert len(df) > 0
    assert 'subject_id' in df.columns
    
    # Validate JSON content
    with open(json_path, 'r') as f:
        meta = json.load(f)
    assert 'matching_strategy' in meta
    assert 'matched_count' in meta
    assert meta['matched_count'] > 0
    assert meta['matched_count'] <= meta['total_microbiome']
    assert meta['matched_count'] <= meta['total_sleep']