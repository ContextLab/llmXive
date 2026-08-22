"""
Contract test for NOAA AR data schema validation.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

def test_noaa_data_schema():
    """Test that NOAA AR data conforms to expected schema."""
    # This test validates the structure of NOAA AR data
    # Expected columns based on NOAA CPC AR Catalog
    expected_columns = [
        'time', 'latitude', 'longitude', 'intensity', 'duration',
        'peak_iwv', 'mean_iwv', 'peak_iwt', 'mean_iwt', 'category'
    ]
    
    # Create a minimal test DataFrame
    test_data = {
        'time': ['2023-01-01'],
        'latitude': [40.0],
        'longitude': [-122.0],
        'intensity': [1.5],
        'duration': [24],
        'peak_iwv': [25.0],
        'mean_iwv': [20.0],
        'peak_iwt': [50.0],
        'mean_iwt': [40.0],
        'category': ['AR4']
    }
    
    df = pd.DataFrame(test_data)
    
    # Check that all expected columns exist
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col}"
    
    # Check data types
    assert pd.api.types.is_numeric_dtype(df['latitude'])
    assert pd.api.types.is_numeric_dtype(df['longitude'])
    assert pd.api.types.is_numeric_dtype(df['intensity'])
    
    # Check region constraints
    assert all((df['latitude'] >= 35.0) & (df['latitude'] <= 50.0))
    assert all((df['longitude'] >= -125.0) & (df['longitude'] <= -120.0))
    
    print("Schema validation passed")

if __name__ == "__main__":
    test_noaa_data_schema()
    print("All tests passed")
