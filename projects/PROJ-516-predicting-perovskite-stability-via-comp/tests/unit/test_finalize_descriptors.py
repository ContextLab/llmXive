"""
Unit tests for finalize_descriptors.py (T017).
Tests the merging of uncertainty flags and the final save logic.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Import the module under test
# We need to adjust the import path based on how tests are run
# Assuming tests are run from project root or code dir
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from finalize_descriptors import merge_uncertainty, load_uncertainty_flags, load_descriptors

def test_merge_uncertainty_list_format():
    """Test merging when flags are a list of dicts with 'id' and 'T_d_uncertainty'."""
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'feature1': [10.0, 20.0, 30.0]
    })
    flags = [
        {'id': 1, 'T_d_uncertainty': 5.0},
        {'id': 2, 'T_d_uncertainty': 10.0},
        {'id': 3, 'T_d_uncertainty': 10.0} # Default
    ]
    
    result = merge_uncertainty(df, flags)
    
    assert 'T_d_uncertainty' in result.columns
    assert result.loc[result['id'] == 1, 'T_d_uncertainty'].values[0] == 5.0
    assert result.loc[result['id'] == 2, 'T_d_uncertainty'].values[0] == 10.0
    assert result.loc[result['id'] == 3, 'T_d_uncertainty'].values[0] == 10.0

def test_merge_uncertainty_dict_format():
    """Test merging when flags are a dict {id: uncertainty}."""
    df = pd.DataFrame({
        'id': ['A', 'B'],
        'feature1': [1.0, 2.0]
    })
    flags = {
        'A': 5.0,
        'B': 10.0
    }
    
    result = merge_uncertainty(df, flags)
    
    assert 'T_d_uncertainty' in result.columns
    assert result.loc[result['id'] == 'A', 'T_d_uncertainty'].values[0] == 5.0
    assert result.loc[result['id'] == 'B', 'T_d_uncertainty'].values[0] == 10.0

def test_merge_uncertainty_missing_id():
    """Test that merge fails gracefully if 'id' column is missing."""
    df = pd.DataFrame({
        'feature1': [1.0, 2.0]
    })
    flags = {'1': 5.0}
    
    with pytest.raises(ValueError, match="No 'id' column"):
        merge_uncertainty(df, flags)

def test_merge_uncertainty_nested_dict_format():
    """Test merging when flags are a dict {id: {uncertainty_key: value}}."""
    df = pd.DataFrame({
        'id': ['X', 'Y'],
        'feature1': [1.0, 2.0]
    })
    flags = {
        'X': {'T_d_uncertainty': 2.5},
        'Y': {'T_d_uncertainty': 7.5}
    }
    
    result = merge_uncertainty(df, flags)
    
    assert 'T_d_uncertainty' in result.columns
    assert result.loc[result['id'] == 'X', 'T_d_uncertainty'].values[0] == 2.5
    assert result.loc[result['id'] == 'Y', 'T_d_uncertainty'].values[0] == 7.5

def test_merge_uncertainty_index_fallback():
    """Test merging by index when no 'id' column but lists match."""
    df = pd.DataFrame({
        'feature1': [1.0, 2.0]
    })
    flags = [
        {'T_d_uncertainty': 5.0},
        {'T_d_uncertainty': 10.0}
    ]
    
    result = merge_uncertainty(df, flags)
    
    assert 'T_d_uncertainty' in result.columns
    assert result['T_d_uncertainty'].iloc[0] == 5.0
    assert result['T_d_uncertainty'].iloc[1] == 10.0
