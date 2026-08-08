import pytest
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data.preprocess import stratify_routes

def test_stratify_routes_empty():
    """Test that stratify_routes raises an error on empty input."""
    with pytest.raises(ValueError, match="Input data is empty"):
        stratify_routes([])

def test_stratify_routes_categories():
    """Test that routes are correctly categorized by stop count."""
    # Create mock data
    data = [
        {"route_id": "r1", "stops": [{"name": "A"}] * 10},       # Short (<15)
        {"route_id": "r2", "stops": [{"name": "A"}] * 20},       # Medium (15-30)
        {"route_id": "r3", "stops": [{"name": "A"}] * 35},       # Long (>30)
        {"route_id": "r4", "stops": [{"name": "A"}] * 14},       # Short (boundary)
        {"route_id": "r5", "stops": [{"name": "A"}] * 15},       # Medium (boundary)
        {"route_id": "r6", "stops": [{"name": "A"}] * 30},       # Medium (boundary)
    ]
    
    df = stratify_routes(data)
    
    assert len(df) == 6
    assert df.loc[df['route_id'] == 'r1', 'length_category'].values[0] == 'short'
    assert df.loc[df['route_id'] == 'r2', 'length_category'].values[0] == 'medium'
    assert df.loc[df['route_id'] == 'r3', 'length_category'].values[0] == 'long'
    assert df.loc[df['route_id'] == 'r4', 'length_category'].values[0] == 'short'
    assert df.loc[df['route_id'] == 'r5', 'length_category'].values[0] == 'medium'
    assert df.loc[df['route_id'] == 'r6', 'length_category'].values[0] == 'medium'
    
    # Verify stop counts
    assert df.loc[df['route_id'] == 'r1', 'stop_count'].values[0] == 10
    assert df.loc[df['route_id'] == 'r3', 'stop_count'].values[0] == 35

def test_stratify_routes_row_count_assertion():
    """Test that the function asserts row_count > 0."""
    # This is implicitly tested by the empty test raising ValueError,
    # but we verify the logic here too.
    data = [{"route_id": "x", "stops": [{"name": "A"}]}]
    df = stratify_routes(data)
    assert len(df) > 0

def test_stratify_routes_output_columns():
    """Test that the output DataFrame has the expected columns."""
    data = [{"route_id": "test", "stops": [{"name": "A"}]}]
    df = stratify_routes(data)
    
    expected_columns = ['route_id', 'stop_count', 'length_category', 'stops', 'city', 'ground_truth_next']
    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"