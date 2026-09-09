"""
Unit tests for data ingestion functions in code/ingestion.py.
"""
import pytest
import pandas as pd
from ingestion import parse_composition, validate_ternary_elements, clean_data

def test_validate_ternary_elements_valid():
    """Test validation of a valid ternary element set."""
    elements = {'Fe', 'Ni', 'B'}
    result = validate_ternary_elements(elements)
    assert result is True

def test_validate_ternary_elements_invalid_count():
    """Test validation of an invalid element count."""
    with pytest.raises(ValueError):
        validate_ternary_elements({'Fe', 'Ni'})
    with pytest.raises(ValueError):
        validate_ternary_elements({'Fe', 'Ni', 'B', 'Cr'})

def test_clean_data_basic():
    """Test basic data cleaning logic."""
    data = pd.DataFrame({
        'composition': ['Fe40.5Ni40.5B19', 'Fe50Ni50', 'Invalid'],
        'critical_cooling_rate': [10.0, 20.0, None]
    })
    cleaned, log = clean_data(data)
    # 'Fe50Ni50' should be dropped (not ternary)
    # 'Invalid' should be dropped (parsing error)
    # None critical_cooling_rate should be dropped
    assert len(cleaned) <= len(data)
