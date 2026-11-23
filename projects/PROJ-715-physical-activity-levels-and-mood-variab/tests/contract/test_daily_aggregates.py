"""
Contract tests for the daily_aggregates.csv output.

These tests verify that the output file conforms to the expected schema.
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_path
from output_validator import load_schema, validate_dataframe

@pytest.fixture
def daily_aggregates_path():
    return get_path("data/processed") / "daily_aggregates.csv"

def test_daily_aggregates_schema(daily_aggregates_path):
    """
    Test that daily_aggregates.csv exists and conforms to the schema.
    """
    # Construct the schema path relative to the project root
    # The schema is located in specs/001-physical-activity-levels-and-mood-variability/contracts/
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-physical-activity-levels-and-mood-variability" / "contracts" / "daily_aggregates.schema.yaml"
    
    assert daily_aggregates_path.exists(), f"File {daily_aggregates_path} does not exist."
    
    schema = load_schema(schema_path)
    df = pd.read_csv(daily_aggregates_path)
    
    # Validate against schema
    is_valid, errors = validate_dataframe(df, schema)
    
    assert is_valid, f"Schema validation failed: {errors}"
    
    # Additional checks
    assert "participant_id" in df.columns, "Missing 'participant_id' column."
    assert "date" in df.columns, "Missing 'date' column."
    assert "total_steps" in df.columns, "Missing 'total_steps' column."
    assert "mean_mood" in df.columns, "Missing 'mean_mood' column."
    assert "mood_std" in df.columns, "Missing 'mood_std' column."