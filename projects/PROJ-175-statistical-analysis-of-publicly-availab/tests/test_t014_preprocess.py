"""
Tests for T014: Normalization and Functional Role Derivation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.preprocess import (
    levenshtein_distance,
    normalize_ingredient_name,
    calculate_functional_role,
    verify_exclusion_of_co_occurrence
)

def test_levenshtein_distance():
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("flaw", "lawn") == 2
    assert levenshtein_distance("same", "same") == 0
    assert levenshtein_distance("", "abc") == 3

def test_normalize_ingredient_name():
    reference = ["tomato", "onion", "garlic", "salt", "pepper"]
    assert normalize_ingredient_name("tomato", reference, threshold=2) == "tomato"
    assert normalize_ingredient_name("tmatto", reference, threshold=2) == "tomato"
    assert normalize_ingredient_name("onions", reference, threshold=2) == "onion"
    assert normalize_ingredient_name("garlck", reference, threshold=2) == "garlic"
    assert normalize_ingredient_name("unknown", reference, threshold=2) is None

def test_calculate_functional_role():
    data = {
        'normalized_ingredient': ['a', 'b', 'c', 'd'],
        'marginal_frequency': [0.5, 0.2, 0.05, 0.01],
        'avg_position': [2.0, 4.0, 10.0, 15.0]
    }
    df = pd.DataFrame(data)
    result = calculate_functional_role(df, freq_threshold=0.1, pos_threshold=5.0)
    
    assert result.loc[result['normalized_ingredient'] == 'a', 'functional_role'].values[0] == 'primary'
    assert result.loc[result['normalized_ingredient'] == 'b', 'functional_role'].values[0] == 'secondary'
    assert result.loc[result['normalized_ingredient'] == 'c', 'functional_role'].values[0] == 'garnish'
    assert result.loc[result['normalized_ingredient'] == 'd', 'functional_role'].values[0] == 'garnish'

def test_verify_exclusion_of_co_occurrence():
    data = {
        'normalized_ingredient': ['a'],
        'marginal_frequency': [0.5],
        'avg_position': [2.0],
        'functional_role': ['primary']
    }
    df = pd.DataFrame(data)
    assert verify_exclusion_of_co_occurrence(df) is True