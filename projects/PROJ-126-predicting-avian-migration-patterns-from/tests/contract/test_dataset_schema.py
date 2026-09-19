import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import DATA_PROCESSED

def test_first_arrival_sweep_schema():
    """Contract test: Verify the schema of first_arrival_sweep.csv."""
    output_file = DATA_PROCESSED / "first_arrival_sweep.csv"
    
    # If file doesn't exist, we assume the pipeline hasn't run yet.
    # In a real CI, this might fail or skip.
    if not output_file.exists():
        pytest.skip("Output file not found. Run T014 first.")
    
    df = pd.read_csv(output_file)
    
    # Expected schema
    expected_columns = ['grid_id', 'week', 'arrival_date_3', 'arrival_date_5', 'arrival_date_10', 'status']
    expected_types = {
        'grid_id': 'object',
        'week': 'object', # or datetime depending on CSV read
        'arrival_date_3': 'object', # datetime
        'arrival_date_5': 'object',
        'arrival_date_10': 'object',
        'status': 'object'
    }
    
    assert list(df.columns) == expected_columns, f"Schema mismatch: {list(df.columns)}"
    
    # Check status values
    valid_statuses = {'determined', 'undetermined'}
    assert set(df['status'].unique()).issubset(valid_statuses), f"Invalid status values: {df['status'].unique()}"