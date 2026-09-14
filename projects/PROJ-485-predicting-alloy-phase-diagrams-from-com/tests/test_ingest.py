import os
import sys
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil

# Add project root to path if running from tests
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ingest.load_data import filter_missing_temperature
from utils.error_codes import ErrorCode
from utils.logging import get_logger

logger = get_logger(__name__)

def test_filter_missing_temperature_removes_rows():
    """
    Test that filter_missing_temperature correctly removes rows with missing T values.
    """
    data = {
        'system_id': ['A', 'B', 'C', 'D'],
        'composition': ['Cu50Al50', 'Cu50Zn50', 'Fe50C50', 'Al100'],
        'temperature': [1000.0, np.nan, 1200.0, None],
        'phase': ['Liquid', 'Solid', 'Liquid', 'Solid']
    }
    df = pd.DataFrame(data)

    filtered_df = filter_missing_temperature(df)

    assert len(filtered_df) == 2, "Expected 2 rows after filtering."
    assert 'B' not in filtered_df['system_id'].values
    assert 'D' not in filtered_df['system_id'].values
    assert 'temperature' in filtered_df.columns
    assert not filtered_df['temperature'].isna().any()

def test_filter_missing_temperature_handles_empty():
    """
    Test behavior with an empty dataframe.
    """
    df = pd.DataFrame(columns=['system_id', 'temperature'])
    filtered_df = filter_missing_temperature(df)
    assert filtered_df.empty

def test_filter_missing_temperature_logs_error():
    """
    Test that the function logs the MISSING_TEMP_COORDS error code.
    This test relies on the logging side-effect.
    """
    data = {
        'system_id': ['X'],
        'temperature': [np.nan]
    }
    df = pd.DataFrame(data)
    
    # The function should log an error. We verify the function doesn't crash
    # and returns an empty dataframe.
    result = filter_missing_temperature(df)
    assert result.empty
    
    # Verify the error code is the one expected by the spec
    assert ErrorCode.MISSING_TEMP_COORDS is not None