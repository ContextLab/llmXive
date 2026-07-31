"""
Contract tests for data schema validation.

Verifies that generated and processed data files strictly adhere to the
schema defined in `data-model.md` and the project's data contracts.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Import project utilities if needed for validation
# from utils import load_json

REQUIRED_COLUMNS = [
    "participant_id",
    "status_level",
    "observed_behavior",
    "risk_taking_score"
]

VALID_STATUS_LEVELS = {"High", "Low"}
VALID_BEHAVIORS = {"Risky", "Conservative"}

def test_raw_data_schema(raw_data_path):
    """
    Verify that the raw synthetic data CSV contains all required columns
    and correct data types.
    """
    assert os.path.exists(raw_data_path), f"Raw data file not found at {raw_data_path}"
    
    df = pd.read_csv(raw_data_path)
    
    # Check columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns in raw data: {missing_cols}"
    
    # Check participant_id uniqueness (between-subjects design)
    assert df["participant_id"].is_unique, "Participant IDs must be unique in between-subjects design"
    
    # Check basic types (pandas usually infers these correctly, but we verify)
    assert df["risk_taking_score"].dtype in ["float64", "int64"], "Risk score should be numeric"

def test_processed_data_schema(processed_data_path):
    """
    Verify that the processed data CSV maintains required columns and
    correctly maps categorical factors.
    """
    assert os.path.exists(processed_data_path), f"Processed data file not found at {processed_data_path}"
    
    df = pd.read_csv(processed_data_path)
    
    # Check columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns in processed data: {missing_cols}"
    
    # Verify categorical integrity
    unique_status = set(df["status_level"].unique())
    assert unique_status.issubset(VALID_STATUS_LEVELS), f"Invalid status levels found: {unique_status - VALID_STATUS_LEVELS}"
    
    unique_behavior = set(df["observed_behavior"].unique())
    assert unique_behavior.issubset(VALID_BEHAVIORS), f"Invalid behaviors found: {unique_behavior - VALID_BEHAVIORS}"
    
    # Check N count (should be same as raw if no dropping, or less if imputation/exclusion)
    assert len(df) > 0, "Processed dataframe is empty"
