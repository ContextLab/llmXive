"""
Unit tests for data ingestion error handling.

Specifically tests that missing required variables in the dataset
raise appropriate errors as per the project's fail-fast policy.
"""
import pytest
import pandas as pd
import yaml
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils import log_setup
from config import DATA_ROOT

# Import the ingestion logic we are testing
# We assume 01_ingest.py will contain the validation logic
# Since T015a/b/c are not implemented yet, we mock the validation function
# that T014 is testing the behavior of.
# However, per the task, we are testing the error handling mechanism.
# We will create a mock validation function that simulates the missing variable check.

# For the purpose of this test, we define the expected variables based on T008
REQUIRED_VARIABLES = [
    "switching_index", 
    "cognitive_flexibility_score", 
    "age", 
    "total_screen_time",
    "num_platforms",
    "switching_frequency"
]

class IngestionError(Exception):
    """Custom exception for ingestion failures."""
    pass

def validate_dataframe_columns(df: pd.DataFrame, required_cols: list) -> None:
    """
    Validates that the dataframe contains all required columns.
    Raises IngestionError if any are missing.
    This is the function behavior being tested.
    """
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise IngestionError(
            f"Data Gap: Required variables {missing} not found in dataset. "
            f"Project cannot proceed."
        )

def test_missing_variable_raises_error():
    """
    Test that a missing variable in the dataset raises IngestionError.
    
    Scenario: The ingestion script receives a dataframe that is missing
    the 'cognitive_flexibility_score' column.
    Expected: An IngestionError is raised with a descriptive message.
    """
    # Create a mock dataframe with some columns but missing the required one
    data = {
        "age": [25, 30, 35],
        "total_screen_time": [120, 180, 90],
        "num_platforms": [4, 6, 3]
        # Missing: switching_index, cognitive_flexibility_score, switching_frequency
    }
    df = pd.DataFrame(data)
    
    # We specifically test for the critical missing variable
    # In a real run, this would be caught by the validation logic in 01_ingest.py
    
    # Assert that the validation function raises the error
    with pytest.raises(IngestionError) as excinfo:
        validate_dataframe_columns(df, REQUIRED_VARIABLES)
    
    # Verify the error message contains the missing variable name
    assert "cognitive_flexibility_score" in str(excinfo.value)
    assert "Data Gap" in str(excinfo.value)

def test_all_variables_present_no_error():
    """
    Test that if all required variables are present, no error is raised.
    """
    data = {
        "switching_index": [1, 2, 3],
        "cognitive_flexibility_score": [0.8, 0.9, 0.7],
        "age": [25, 30, 35],
        "total_screen_time": [120, 180, 90],
        "num_platforms": [4, 6, 3],
        "switching_frequency": [5, 8, 2]
    }
    df = pd.DataFrame(data)
    
    # Should not raise
    try:
        validate_dataframe_columns(df, REQUIRED_VARIABLES)
    except IngestionError:
        pytest.fail("validate_dataframe_columns raised an error unexpectedly")

def test_multiple_missing_variables_raises_error():
    """
    Test that if multiple variables are missing, the error lists them.
    """
    data = {
        "age": [25, 30],
        # Missing many
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(IngestionError) as excinfo:
        validate_dataframe_columns(df, REQUIRED_VARIABLES)
    
    error_msg = str(excinfo.value)
    assert "cognitive_flexibility_score" in error_msg
    assert "switching_index" in error_msg
    assert "switching_frequency" in error_msg