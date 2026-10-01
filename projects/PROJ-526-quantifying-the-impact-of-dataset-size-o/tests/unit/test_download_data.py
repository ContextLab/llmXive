"""
Unit tests for download_data module.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.dirname(__file__), '..', '..', 'code'))

from download_data import (
    exponential_backoff,
    optimize_dataframe_dtypes,
    DownloadError
)

def test_exponential_backoff():
    """Test exponential backoff delay calculation."""
    # First retry
    delay = exponential_backoff(0)
    assert delay == 1.0
    
    # Second retry
    delay = exponential_backoff(1)
    assert delay == 2.0
    
    # Third retry
    delay = exponential_backoff(2)
    assert delay == 4.0
    
    # Should cap at max_delay
    delay = exponential_backoff(10)
    assert delay == 60.0

def test_optimize_dataframe_dtypes():
    """Test dtype optimization for dataframes."""
    import pandas as pd
    import numpy as np
    
    # Create test dataframe
    df = pd.DataFrame({
        'large_float': [1.0, 2.0, 3.0] * 1000,
        'small_int': [1, 2, 3] * 1000,
        'category_col': ['a', 'b', 'c'] * 1000
    })
    
    # Optimize dtypes
    optimized_df = optimize_dataframe_dtypes(df)
    
    # Check that optimization was applied
    assert optimized_df['small_int'].dtype in ['int8', 'int16', 'int32']
    assert optimized_df['category_col'].dtype == 'category'

def test_download_error():
    """Test DownloadError exception."""
    with pytest.raises(DownloadError) as exc_info:
        raise DownloadError("Test error")
    
    assert str(exc_info.value) == "Test error"
