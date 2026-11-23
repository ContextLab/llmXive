"""
Unit tests for data_utils module.
"""
import pandas as pd
import numpy as np
import pytest
from code.utils.data_utils import validate_coordinates, check_data_quality

def test_validate_coordinates():
    """Test coordinate validation."""
    data = {
        'decimalLongitude': [-100, 200, -90],
        'decimalLatitude': [30, 40, 100]
    }
    df = pd.DataFrame(data)
    result = validate_coordinates(df)

    # Should filter out invalid coordinates
    assert len(result) < len(df)
    assert all((result['decimalLongitude'] >= -180) & (result['decimalLongitude'] <= 180))

def test_check_data_quality():
    """Test data quality check."""
    data = {
        'decimalLongitude': [-100, -90],
        'decimalLatitude': [30, 35],
        'species': ['A', 'B']
    }
    df = pd.DataFrame(data)
    quality = check_data_quality(df, required_cols=['species'])

    assert 'missing_counts' in quality
    assert quality['total_records'] == 2
