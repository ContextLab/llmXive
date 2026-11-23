"""
Unit tests for the validation module (T032a).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from code.validation import compute_direction_match, calculate_correlations

def test_compute_direction_match():
    """
    Test direction matching logic.
    """
    # Create mock original results
    original_df = pd.DataFrame({
        'taxon': ['TaxonA', 'TaxonB', 'TaxonC'],
        'coef': [0.5, -0.3, 0.1],
        'qval': [0.01, 0.02, 0.04]
    })
    
    # Create mock validation correlations
    validation_corrs = pd.Series({
        'TaxonA': 0.6,   # Match (both positive)
        'TaxonB': -0.2,  # Match (both negative)
        'TaxonC': -0.1,  # Mismatch (orig pos, val neg)
        'TaxonD': 0.4    # Not in original
    })
    
    result = compute_direction_match(original_df, validation_corrs, 'phq9')
    
    assert result['common_taxa'] == 3
    assert result['matching_directions'] == 2
    assert result['match_percentage'] == pytest.approx(66.67, rel=0.1)
    assert result['threshold_met'] == False  # 66.67 < 80

def test_compute_direction_match_no_common():
    """
    Test when no common taxa exist.
    """
    original_df = pd.DataFrame({
        'taxon': ['TaxonA'],
        'coef': [0.5],
        'qval': [0.01]
    })
    
    validation_corrs = pd.Series({
        'TaxonB': 0.6
    })
    
    result = compute_direction_match(original_df, validation_corrs, 'phq9')
    
    assert result['common_taxa'] == 0
    assert result['matching_directions'] == 0
    assert result['match_percentage'] == 0.0
    assert result['threshold_met'] == False
