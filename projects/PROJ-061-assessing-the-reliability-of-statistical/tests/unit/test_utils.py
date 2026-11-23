import pandas as pd
import numpy as np
import logging
from io import StringIO

# Import the function to test
from code.utils import handle_missing_values

def test_handle_missing_values_no_missing():
    """Test that a DataFrame with no missing values is returned unchanged."""
    data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    result = handle_missing_values(df, logger)
    
    assert result.shape == df.shape
    assert result.equals(df)

def test_handle_missing_values_some_missing():
    """Test that rows with missing values are dropped (listwise deletion)."""
    data = {
        'A': [1, 2, np.nan, 4, 5],
        'B': [np.nan, 5, 6, 7, 8],
        'C': [9, 10, 11, 12, 13]
    }
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    result = handle_missing_values(df, logger)
    
    # Row 2 (index 2) has NaN in A.
    # Row 0 (index 0) has NaN in B.
    # Rows 1, 3, 4 are complete.
    expected_indices = [1, 3, 4]
    assert list(result.index) == expected_indices
    assert result.shape[0] == 3

def test_handle_missing_values_all_missing():
    """Test behavior when all rows have at least one missing value."""
    data = {
        'A': [np.nan, 2],
        'B': [1, np.nan]
    }
    df = pd.DataFrame(data)
    
    logger = logging.getLogger("test")
    result = handle_missing_values(df, logger)
    
    assert result.shape[0] == 0
    assert result.shape[1] == 2

def test_handle_missing_values_logging():
    """Test that the function logs the correct message."""
    data = {'A': [1, np.nan, 3], 'B': [4, 5, 6]}
    df = pd.DataFrame(data)
    
    # Capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    logger = logging.getLogger("test_log")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    result = handle_missing_values(df, logger)
    
    log_output = log_stream.getvalue()
    assert "Removed 1 rows with missing values" in log_output
    
    logger.removeHandler(handler)