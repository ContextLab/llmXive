"""
Unit tests for human_coding.py
"""
import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import json
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from human_coding import (
    calculate_fleiss_kappa,
    process_annotations,
    cross_reference_external_validation,
    MIN_ANNOTATORS,
    KAPPA_THRESHOLD
)

def test_calculate_fleiss_kappa_perfect_agreement():
    """Test Fleiss' Kappa with perfect agreement."""
    data = [
        {'scenario_id': 'S1', 'annotator_id': 'A1', 'rating': 1},
        {'scenario_id': 'S1', 'annotator_id': 'A2', 'rating': 1},
        {'scenario_id': 'S1', 'annotator_id': 'A3', 'rating': 1},
        {'scenario_id': 'S2', 'annotator_id': 'A1', 'rating': 2},
        {'scenario_id': 'S2', 'annotator_id': 'A2', 'rating': 2},
        {'scenario_id': 'S2', 'annotator_id': 'A3', 'rating': 2},
    ]
    df = pd.DataFrame(data)
    kappa = calculate_fleiss_kappa(df)
    assert kappa == 1.0

def test_calculate_fleiss_kappa_no_agreement():
    """Test Fleiss' Kappa with no agreement (1-1-1 split)."""
    data = [
        {'scenario_id': 'S1', 'annotator_id': 'A1', 'rating': 1},
        {'scenario_id': 'S1', 'annotator_id': 'A2', 'rating': 2},
        {'scenario_id': 'S1', 'annotator_id': 'A3', 'rating': 3},
        {'scenario_id': 'S2', 'annotator_id': 'A1', 'rating': 1},
        {'scenario_id': 'S2', 'annotator_id': 'A2', 'rating': 2},
        {'scenario_id': 'S2', 'annotator_id': 'A3', 'rating': 3},
    ]
    df = pd.DataFrame(data)
    kappa = calculate_fleiss_kappa(df)
    # Kappa should be low, potentially negative or zero depending on chance
    assert kappa < 0.5

def test_process_annotations_majority_vote():
    """Test majority vote logic."""
    data = [
        {'scenario_id': 'S1', 'annotator_id': 'A1', 'rating': 3},
        {'scenario_id': 'S1', 'annotator_id': 'A2', 'rating': 3},
        {'scenario_id': 'S1', 'annotator_id': 'A3', 'rating': 4}, # Majority 3
        {'scenario_id': 'S2', 'annotator_id': 'A1', 'rating': 1},
        {'scenario_id': 'S2', 'annotator_id': 'A2', 'rating': 2},
        {'scenario_id': 'S2', 'annotator_id': 'A3', 'rating': 3}, # No majority
        {'scenario_id': 'S3', 'annotator_id': 'A1', 'rating': 5},
        {'scenario_id': 'S3', 'annotator_id': 'A2', 'rating': 5},
        {'scenario_id': 'S3', 'annotator_id': 'A3', 'rating': 5}, # Unanimous
    ]
    df = pd.DataFrame(data)
    result, kappa = process_annotations(df)
    
    assert 'S1' in result['scenario_id'].values
    assert result.loc[result['scenario_id'] == 'S1', 'final_rating'].iloc[0] == 3
    
    assert 'S2' not in result['scenario_id'].values # Excluded due to no majority
    
    assert 'S3' in result['scenario_id'].values
    assert result.loc[result['scenario_id'] == 'S3', 'final_rating'].iloc[0] == 5

def test_process_annotations_insufficient_annotators():
    """Test exclusion of scenarios with < MIN_ANNOTATORS."""
    data = [
        {'scenario_id': 'S1', 'annotator_id': 'A1', 'rating': 3},
        {'scenario_id': 'S1', 'annotator_id': 'A2', 'rating': 3},
        # Only 2 annotators
    ]
    df = pd.DataFrame(data)
    result, kappa = process_annotations(df)
    assert result.empty

def test_cross_reference_external_validation():
    """Test cross-referencing with external validation."""
    scenario_ids = ['S1', 'S2', 'S3']
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'S1': {'is_ambiguous': True},
            'S3': {'is_ambiguous': False} # Should be excluded
        }, f)
        temp_path = f.name
    
    try:
        valid_ids = cross_reference_external_validation(scenario_ids, temp_path)
        assert 'S1' in valid_ids
        assert 'S2' in valid_ids # Not in external file, so kept (fallback)
        assert 'S3' not in valid_ids
    finally:
        os.unlink(temp_path)