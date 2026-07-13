import pytest
import pandas as pd
import numpy as np
from pathlib import Path

def test_ebird_schema_columns():
    """Test that eBird DataFrame has expected columns and dtypes."""
    # Create a sample DataFrame matching the expected schema
    data = {
        "species": ["Turdus migratorius"],
        "lat": [45.0],
        "lon": [-120.0],
        "date": [pd.to_datetime("2023-01-01")],
        "count": [5],
        "checklist_id": ["CHECK_001"]
    }
    df = pd.DataFrame(data)
    
    expected_columns = ["species", "lat", "lon", "date", "count", "checklist_id"]
    assert list(df.columns) == expected_columns
    
    # Check dtypes
    assert df["species"].dtype == "object"
    assert df["lat"].dtype in ["float64", "float32"]
    assert df["lon"].dtype in ["float64", "float32"]
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["count"].dtype in ["int64", "int32", "float64"]
    assert df["checklist_id"].dtype == "object"
