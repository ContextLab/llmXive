"""
T035a [US1] Validate schema of data/processed/features_clr.csv.
Tests: no nulls, correct columns, valid RT range.
"""
import os
import pytest
import pandas as pd
from pathlib import Path
from config import get_path, get_all_band_names, get_epsilon

def load_features():
    path = get_path("processed", "features_clr.csv")
    if not os.path.exists(path):
        pytest.skip(f"File not found: {path}")
    return pd.read_csv(path)

def test_columns_present():
    df = load_features()
    required = ['participant_id', 'median_rt']
    bands = get_all_band_names()
    expected_cols = required + [f'clr_{b}' for b in bands]

    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"

def test_no_nulls():
    df = load_features()
    # Check numeric columns for nulls
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        assert not df[col].isnull().any(), f"Nulls found in {col}"

def test_rt_range():
    df = load_features()
    # FR-004: 100ms to 2000ms
    assert (df['median_rt'] >= 0.1).all(), "RT < 100ms found"
    assert (df['median_rt'] <= 2.0).all(), "RT > 2000ms found"

def test_clr_values_reasonable():
    df = load_features()
    bands = get_all_band_names()
    clr_cols = [f'clr_{b}' for b in bands]
    for col in clr_cols:
        # CLR values can be negative, but should not be extreme (e.g. < -20 or > 20)
        assert (df[col] > -20).all(), f"Extreme negative CLR in {col}"
        assert (df[col] < 20).all(), f"Extreme positive CLR in {col}"
