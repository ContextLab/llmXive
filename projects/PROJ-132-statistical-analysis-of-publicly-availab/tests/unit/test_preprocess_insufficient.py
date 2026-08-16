import pytest
import polars as pl
from pathlib import Path
import tempfile
import json
from src.data.preprocess import mark_insufficient_cells, MIN_OBSERVATIONS

@pytest.fixture
def sample_data():
    """Create a sample Polars DataFrame for testing."""
    data = {
        "species": ["A", "A", "B", "B"],
        "grid_cell": ["45.0_-120.5", "45.0_-120.5", "46.0_-121.0", "46.0_-121.0"],
        "year": [2020, 2020, 2020, 2020],
        "week": [10, 10, 10, 10],
        "observation_count": [5, 15, 8, 20],  # Some below MIN, some above
        "first_arrival_date": [None, None, None, None],
        "median_arrival_date": [None, None, None, None],
        "stopover_duration": [None, None, None, None]
    }
    return pl.DataFrame(data)

def test_mark_insufficient_cells_logic(sample_data):
    """Test that mark_insufficient_cells correctly flags rows based on MIN_OBSERVATIONS."""
    result = mark_insufficient_cells(sample_data)
    
    assert "data_quality" in result.columns
    
    # Row 0: count=5 < MIN (default 10) -> insufficient
    assert result[0, "data_quality"] == "insufficient"
    # Row 1: count=15 >= MIN -> sufficient
    assert result[1, "data_quality"] == "sufficient"
    # Row 2: count=8 < MIN -> insufficient
    assert result[2, "data_quality"] == "insufficient"
    # Row 3: count=20 >= MIN -> sufficient
    assert result[3, "data_quality"] == "sufficient"

def test_mark_insufficient_cells_output_schema(sample_data):
    """Verify the output schema includes all original columns plus data_quality."""
    result = mark_insufficient_cells(sample_data)
    
    expected_cols = set(sample_data.columns) | {"data_quality"}
    assert set(result.columns) == expected_cols
    
    # Verify types
    assert result.schema["data_quality"] == pl.Utf8

def test_mark_insufficient_cells_edge_case_zero():
    """Test behavior when observation_count is 0."""
    data = {
        "species": ["A"],
        "grid_cell": ["45.0_-120.5"],
        "year": [2020],
        "week": [10],
        "observation_count": [0],
        "first_arrival_date": [None],
        "median_arrival_date": [None],
        "stopover_duration": [None]
    }
    df = pl.DataFrame(data)
    result = mark_insufficient_cells(df)
    
    assert result[0, "data_quality"] == "insufficient"

def test_mark_insufficient_cells_exact_threshold():
    """Test behavior when observation_count equals MIN_OBSERVATIONS exactly."""
    data = {
        "species": ["A"],
        "grid_cell": ["45.0_-120.5"],
        "year": [2020],
        "week": [10],
        "observation_count": [MIN_OBSERVATIONS],
        "first_arrival_date": [None],
        "median_arrival_date": [None],
        "stopover_duration": [None]
    }
    df = pl.DataFrame(data)
    result = mark_insufficient_cells(df)
    
    # Should be sufficient (>=)
    assert result[0, "data_quality"] == "sufficient"