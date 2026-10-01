import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the function to test
from code.derive_dilemma_complexity import calculate_complexity_score, derive_complexity

def test_calculate_complexity_score_basic():
    """Test basic complexity calculation with known values."""
    # Create a mock row with standard column names
    row_data = {
        'number_of_people_left': 1,
        'number_of_people_right': 5,
        'pedestrians_left': 1,
        'pedestrians_right': 0
    }
    row = pd.Series(row_data)
    
    complexity = calculate_complexity_score(row)
    
    # Expected: 1 + 5 = 6 (base) + 0.2 (disparity: 1/5 < 0.3) + 0.5 (pedestrians) = 6.7
    assert complexity == pytest.approx(6.7, rel=1e-5)

def test_calculate_complexity_score_no_pedestrians():
    """Test complexity calculation without pedestrians."""
    row_data = {
        'number_of_people_left': 2,
        'number_of_people_right': 2,
    }
    row = pd.Series(row_data)
    
    complexity = calculate_complexity_score(row)
    
    # Expected: 2 + 2 = 4 (base) + 0.0 (no disparity, 2/2 = 1.0) + 0.0 (no pedestrians) = 4.0
    assert complexity == pytest.approx(4.0, rel=1e-5)

def test_calculate_complexity_score_missing_columns():
    """Test complexity calculation when standard columns are missing."""
    # Mock row with no standard columns
    row_data = {
        'other_column': 10,
        'participant_id': 123
    }
    row = pd.Series(row_data)
    
    complexity = calculate_complexity_score(row)
    
    # Expected: 0 (no lives found) + 0.0 + 0.0 = 0.0
    assert complexity == pytest.approx(0.0, rel=1e-5)

def test_derive_complexity_dataframe():
    """Test deriving complexity for a full dataframe."""
    df_data = {
        'participant_id': [1, 2, 3],
        'dilemma_id': ['A', 'B', 'C'],
        'number_of_people_left': [1, 2, 1],
        'number_of_people_right': [5, 2, 3],
        'pedestrians_left': [1, 0, 1],
        'pedestrians_right': [0, 0, 0]
    }
    df = pd.DataFrame(df_data)
    
    df_result = derive_complexity(df)
    
    # Check that the new column exists
    assert 'dilemma_complexity' in df_result.columns
    
    # Check the values
    # Row 0: 1+5=6 + 0.2 (disparity) + 0.5 (ped) = 6.7
    # Row 1: 2+2=4 + 0.0 (no disparity) + 0.0 = 4.0
    # Row 2: 1+3=4 + 0.2 (disparity: 1/3 < 0.3) + 0.5 (ped) = 4.7
    assert df_result.iloc[0]['dilemma_complexity'] == pytest.approx(6.7, rel=1e-5)
    assert df_result.iloc[1]['dilemma_complexity'] == pytest.approx(4.0, rel=1e-5)
    assert df_result.iloc[2]['dilemma_complexity'] == pytest.approx(4.7, rel=1e-5)

def test_derive_complexity_preserves_original():
    """Test that derive_complexity does not modify the original dataframe."""
    df_data = {
        'participant_id': [1],
        'number_of_people_left': [1],
        'number_of_people_right': [5]
    }
    df_original = pd.DataFrame(df_data)
    df_copy = df_original.copy()
    
    derive_complexity(df_original)
    
    # Check that the original dataframe is unchanged
    assert df_original.equals(df_copy)
    # Check that the result has the new column
    df_result = derive_complexity(df_copy)
    assert 'dilemma_complexity' in df_result.columns