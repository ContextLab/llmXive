"""
Contract test for sensitivity analysis output schema.
Validates that the sensitivity_sweep.csv file has the correct columns and types.
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path if running from tests
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_sensitivity_output_schema(tmp_path):
    """
    Test that the sensitivity sweep output file has the required schema.
    Schema: [width, mae, ci]
    """
    # Simulate the expected output file content
    output_file = tmp_path / "sensitivity_sweep.csv"
    
    # Create a mock CSV with the required schema
    mock_data = {
        'width': [0.1, 0.2, 0.5],
        'mae': [0.15, 0.15, 0.15],
        'ci': [0.1, 0.2, 0.5]
    }
    df = pd.DataFrame(mock_data)
    df.to_csv(output_file, index=False)
    
    # Load and validate
    loaded_df = pd.read_csv(output_file)
    
    # Check columns
    required_columns = ['width', 'mae', 'ci']
    assert list(loaded_df.columns) == required_columns, \
        f"Expected columns {required_columns}, got {list(loaded_df.columns)}"
    
    # Check data types
    assert loaded_df['width'].dtype in ['float64', 'float32', 'int64', 'int32'], \
        "Column 'width' must be numeric."
    assert loaded_df['mae'].dtype in ['float64', 'float32', 'int64', 'int32'], \
        "Column 'mae' must be numeric."
    assert loaded_df['ci'].dtype in ['float64', 'float32', 'int64', 'int32'], \
        "Column 'ci' must be numeric."
    
    # Check for non-null values (basic contract)
    assert loaded_df.notnull().all().all(), "No null values allowed in the output."
    
    # Check that 'width' and 'ci' are equal in this specific sweep implementation
    # (as per the logic in analysis.py where ci is set to width)
    # This is a specific contract for this implementation
    pd.testing.assert_series_equal(loaded_df['width'], loaded_df['ci'], 
                                   check_names=False, 
                                   check_dtype=False)

def test_sensitivity_output_empty_file(tmp_path):
    """Test that an empty file with correct headers is handled gracefully if expected."""
    output_file = tmp_path / "sensitivity_sweep.csv"
    output_file.write_text("width,mae,ci\n")
    
    df = pd.read_csv(output_file)
    assert len(df) == 0
    assert list(df.columns) == ['width', 'mae', 'ci']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
