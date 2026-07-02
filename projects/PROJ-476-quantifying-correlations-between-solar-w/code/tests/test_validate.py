"""
Unit tests for data validation logic in code/data/validate.py.
"""
import pytest
import pandas as pd
import os
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.validate import validate_columns
from code.config import ACE_VARS, NOAA_VARS


def test_fetch_aborts_on_missing_he2plus():
    """
    Verify that validate_columns raises a ValueError with the specific message
    when the 'He2+_ratio' column is missing from the DataFrame.
    """
    # Create a DataFrame with all ACE variables EXCEPT He2+_ratio
    # This simulates a scenario where the source file is missing the required column
    df_missing = pd.DataFrame({
        'N_p': [1.0, 2.0, 3.0],
        'T_p': [100000.0, 110000.0, 120000.0],
        # 'He2+_ratio' is intentionally omitted
        'timestamp': pd.date_range('2020-01-01', periods=3)
    })

    # The task requires checking against ACE_VARS which includes 'He2+_ratio'
    with pytest.raises(ValueError, match="Missing required variable: He2+_ratio"):
        validate_columns(df_missing, ACE_VARS)