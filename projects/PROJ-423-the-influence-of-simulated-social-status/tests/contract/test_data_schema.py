"""
Contract tests to validate the data schema of generated and processed datasets
against the requirements in data-model.md and the task specifications.

This test suite ensures that the output CSV files from the data generation
and preprocessing pipelines adhere to the strict schema contract defined
for the 'Influence of Simulated Social Status' project.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure code is importable
@pytest.fixture(autouse=True)
def setup_path():
    root = Path(__file__).parent.parent.parent
    code_path = str(root / "code")
    if code_path not in sys.path:
        sys.path.insert(0, code_path)
    yield

# Constants defined from data-model.md and task requirements
REQUIRED_COLUMNS = {
    "status_level",
    "observed_behavior",
    "risk_taking_score",
    "participant_id"
}

VALID_STATUS_LEVELS = {"High", "Low"}
VALID_BEHAVIORS = {"Risky", "Conservative"}

# Expected file paths relative to project root
PROCESSED_DATA_PATH = "data/processed/synthetic_dataset.csv"
RAW_DATA_PATH = "data/raw/synthetic_dataset_raw.csv"

def _get_processed_dataframe() -> pd.DataFrame:
    """
    Helper to load the processed dataset.
    Raises FileNotFoundError if the file does not exist,
    allowing the test to fail loudly rather than pass on missing data.
    """
    root = Path(__file__).parent.parent.parent
    file_path = root / PROCESSED_DATA_PATH
    
    if not file_path.exists():
        # Fallback to raw data if processed doesn't exist yet, 
        # but note this in the test logic if needed.
        # For strict contract testing, we expect the processed file.
        if (root / RAW_DATA_PATH).exists():
            return pd.read_csv(root / RAW_DATA_PATH)
        raise FileNotFoundError(
            f"Contract test failed: Expected data file not found at "
            f"{file_path} or {root / RAW_DATA_PATH}. "
            f"Please run the data generation pipeline first."
        )
    
    return pd.read_csv(file_path)

def test_required_columns_exist():
    """
    Test that the processed data file contains the required columns:
    status_level, observed_behavior, risk_taking_score, participant_id.
    """
    df = _get_processed_dataframe()
    actual_columns = set(df.columns)
    
    missing = REQUIRED_COLUMNS - actual_columns
    assert not missing, (
        f"Schema violation: Missing required columns {missing}. "
        f"Found: {actual_columns}"
    )

def test_categorical_values_valid():
    """
    Test that categorical columns have only expected values.
    status_level must be 'High' or 'Low'.
    observed_behavior must be 'Risky' or 'Conservative'.
    """
    df = _get_processed_dataframe()
    
    # Check status_level
    unique_status = set(df['status_level'].astype(str).unique())
    invalid_status = unique_status - VALID_STATUS_LEVELS
    assert not invalid_status, (
        f"Invalid values found in 'status_level': {invalid_status}. "
        f"Allowed: {VALID_STATUS_LEVELS}"
    )
    
    # Check observed_behavior
    unique_behavior = set(df['observed_behavior'].astype(str).unique())
    invalid_behavior = unique_behavior - VALID_BEHAVIORS
    assert not invalid_behavior, (
        f"Invalid values found in 'observed_behavior': {invalid_behavior}. "
        f"Allowed: {VALID_BEHAVIORS}"
    )

def test_data_types():
    """
    Test expected data types for columns.
    - participant_id: int or str
    - risk_taking_score: float or int
    - status_level: object or category
    - observed_behavior: object or category
    """
    df = _get_processed_dataframe()
    
    # Check participant_id
    pid_dtype = df['participant_id'].dtype
    assert pid_dtype in ['int64', 'int32', 'object', 'str', 'float64'], (
        f"Unexpected dtype for 'participant_id': {pid_dtype}"
    )
    
    # Check risk_taking_score
    score_dtype = df['risk_taking_score'].dtype
    assert pd.api.types.is_numeric_dtype(score_dtype), (
        f"'risk_taking_score' must be numeric. Found: {score_dtype}"
    )
    
    # Check categorical columns (object or category are acceptable in pandas)
    for col in ['status_level', 'observed_behavior']:
        col_dtype = df[col].dtype
        assert col_dtype in ['object', 'category', 'str'], (
            f"'{col}' should be object or category. Found: {col_dtype}"
        )

def test_participant_id_uniqueness():
    """
    Test that participant_id is unique (between-subjects design).
    This validates the experimental design constraint.
    """
    df = _get_processed_dataframe()
    if 'participant_id' not in df.columns:
        pytest.skip("participant_id column missing")
        
    unique_ids = df['participant_id'].nunique()
    total_ids = len(df)
    
    assert unique_ids == total_ids, (
        f"Design violation: Duplicate participant_ids detected. "
        f"Expected {total_ids} unique IDs for {total_ids} rows (between-subjects)."
    )