import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path

# Import the functions from the module we just created
# Assuming the test is run from the project root, we need to add code to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocess import (
    normalize_tags,
    parse_dates,
    aggregate_monthly_frequencies,
    filter_min_months
)

def test_normalize_tags():
    """Test that tags are lowercased and trimmed."""
    data = {
        'tag': ['  Python  ', 'RUST', ' java ', ''],
        'creation_date': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01']
    }
    df = pd.DataFrame(data)
    result = normalize_tags(df)
    
    assert list(result['tag']) == ['python', 'rust', 'java']
    assert '' not in result['tag'].values

def test_parse_dates():
    """Test date parsing and year_month extraction."""
    data = {
        'tag': ['python'],
        'creation_date': ['2023-01-15T10:00:00Z', '2023-02-20T12:00:00Z', 'invalid']
    }
    df = pd.DataFrame(data)
    result = parse_dates(df)
    
    assert 'year_month' in result.columns
    assert len(result) == 2  # Invalid date dropped
    assert '2023-01' in result['year_month'].values
    assert '2023-02' in result['year_month'].values

def test_aggregate_monthly_frequencies():
    """Test aggregation of counts per tag per month."""
    data = {
        'tag': ['python', 'python', 'python', 'rust', 'rust'],
        'year_month': ['2023-01', '2023-01', '2023-02', '2023-01', '2023-01']
    }
    df = pd.DataFrame(data)
    result = aggregate_monthly_frequencies(df)
    
    # Check shape
    assert len(result) == 3  # (python, 01), (python, 02), (rust, 01)
    
    # Check specific counts
    python_jan = result[(result['tag'] == 'python') & (result['year_month'] == '2023-01')]
    assert python_jan['count'].values[0] == 2

    rust_jan = result[(result['tag'] == 'rust') & (result['year_month'] == '2023-01')]
    assert rust_jan['count'].values[0] == 2

def test_filter_min_months():
    """Test filtering tags with less than 12 months of data."""
    # Create a mock dataframe where 'python' has 12 months, 'rust' has 11
    tags = []
    months = []
    counts = []
    
    # Python: 12 months
    for i in range(12):
        tags.append('python')
        months.append(f'2023-{str(i+1).zfill(2)}')
        counts.append(10)
    
    # Rust: 11 months
    for i in range(11):
        tags.append('rust')
        months.append(f'2023-{str(i+1).zfill(2)}')
        counts.append(10)
    
    df = pd.DataFrame({'tag': tags, 'year_month': months, 'count': counts})
    
    result = filter_min_months(df)
    
    assert 'rust' not in result['tag'].values
    assert 'python' in result['tag'].values
    assert len(result) == 12  # Only python's 12 rows

if __name__ == '__main__':
    pytest.main([__file__, '-v'])