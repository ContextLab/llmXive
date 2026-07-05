"""
Contract test for data schema validation.
Ensures that downloaded data matches the expected schema.
"""
import pytest
import json
from pathlib import Path
from data.download import download_faostat

def test_faostat_schema():
    """
    Test that FAOSTAT data conforms to the expected schema.
    """
    # Run the download (this might take a while, so we might want to mock in CI)
    # For now, we assume it runs and we check the output
    try:
        output_path = download_faostat("FS") # Food Security
    except NotImplementedError:
        pytest.skip("FAOSTAT download not implemented yet")
    
    assert output_path.exists(), "FAOSTAT output file not found"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Check basic structure
    assert isinstance(data, list), "FAOSTAT data should be a list of records"
    
    if len(data) > 0:
        record = data[0]
        # Check for expected keys based on FAOSTAT API response
        # Typical keys: 'Domain', 'Area', 'Item', 'Element', 'Unit', 'Year', 'Value'
        expected_keys = ['Domain', 'Area', 'Item', 'Element', 'Unit', 'Year', 'Value']
        for key in expected_keys:
            assert key in record, f"Missing expected key: {key}"
    
    # Check data types
    for record in data[:10]: # Check first 10 records
        if 'Year' in record:
            assert isinstance(record['Year'], int), "Year should be an integer"
        if 'Value' in record:
            assert isinstance(record['Value'], (int, float, type(None))), "Value should be numeric or null"
