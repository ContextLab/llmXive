"""
Unit tests for data validation logic.
"""
import pytest
import pandas as pd
from code.data.validate import validate_columns
from code.config import ACE_VARS, NOAA_VARS


def test_fetch_aborts_on_missing_he2plus():
    """
    Verify that validate_columns aborts with a clear error if He2+_ratio is missing.
    
    This test satisfies the requirement in T012 to abort with a clear error
    if N_p, T_p, or He2+_ratio are missing, and to log the specific missing variable.
    """
    # Create a DataFrame with N_p and T_p but missing He2+_ratio
    df_missing_he = pd.DataFrame({
        'N_p': [5.0, 6.0, 7.0],
        'T_p': [100000.0, 110000.0, 120000.0],
        'other_col': [1, 2, 3]
    })
    
    # We expect a ValueError with the specific message for He2+_ratio
    # Note: ACE_VARS is defined as ['N_p', 'T_p', 'He2+_ratio'] in code/config.py
    with pytest.raises(ValueError, match="Missing required variable: He2+_ratio"):
        validate_columns(df_missing_he, ACE_VARS)

def test_fetch_aborts_on_missing_np():
    """
    Verify that validate_columns aborts if N_p is missing.
    """
    df_missing_np = pd.DataFrame({
        'T_p': [100000.0, 110000.0],
        'He2+_ratio': [0.05, 0.06]
    })
    
    with pytest.raises(ValueError, match="Missing required variable: N_p"):
        validate_columns(df_missing_np, ACE_VARS)

def test_fetch_aborts_on_missing_tp():
    """
    Verify that validate_columns aborts if T_p is missing.
    """
    df_missing_tp = pd.DataFrame({
        'N_p': [5.0, 6.0],
        'He2+_ratio': [0.05, 0.06]
    })
    
    with pytest.raises(ValueError, match="Missing required variable: T_p"):
        validate_columns(df_missing_tp, ACE_VARS)

def test_validate_columns_passes():
    """
    Verify that validate_columns passes when all required columns are present.
    """
    df_complete = pd.DataFrame({
        'N_p': [5.0, 6.0],
        'T_p': [100000.0, 110000.0],
        'He2+_ratio': [0.05, 0.06],
        'extra_col': [1, 2]
    })
    
    # Should not raise
    validate_columns(df_complete, ACE_VARS)

def test_validate_noaa_columns():
    """
    Verify validation logic works for NOAA variables as well.
    """
    df_noaa = pd.DataFrame({
        'Kp': [2.0, 3.0],
        'Dst': [-20.0, -30.0]
    })
    
    # Should not raise
    validate_columns(df_noaa, NOAA_VARS)

def test_validate_noaa_missing_dst():
    """
    Verify validation logic fails for missing NOAA variables.
    """
    df_noaa_missing = pd.DataFrame({
        'Kp': [2.0, 3.0]
    })
    
    with pytest.raises(ValueError, match="Missing required variable: Dst"):
        validate_columns(df_noaa_missing, NOAA_VARS)