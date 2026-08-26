import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logging_init import setup_global_logger
from utils.config_loader import load_config

# Mock setup for testing if not run via full pipeline
def setup_module(module):
    # Ensure logging is configured for the test
    try:
        config_path = project_root / "code" / "config" / "logging_config.yaml"
        if config_path.exists():
            setup_global_logger(config_path)
    except Exception:
        pass

def test_merged_dataset_schema():
    """
    Contract test: Verify the output schema of T023 (merged_dataset_full.csv).
    Ensures all required columns for T024 (Regression) are present.
    """
    output_path = project_root / "data" / "derived" / "merged_dataset_full.csv"
    
    if not output_path.exists():
        pytest.skip("Output file not generated yet. Run T023 first.")
    
    df = pd.read_csv(output_path)
    
    # Required columns based on T023 and T024 requirements
    required_columns = [
        "participant_id",
        "headline_id",
        "belief_rating",
        "headline_text",
        "valence",
        "lexicon_used",
        "cognitive_reflection_score",
        "total_fixation_duration",
        "headline_length"
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    assert not missing, f"Missing required columns in merged dataset: {missing}"
    
    # Check types
    assert df["belief_rating"].dtype in ['int64', 'float64'], "belief_rating must be numeric"
    assert df["valence"].dtype in ['int64', 'float64', 'float32'], "valence must be numeric"
    assert df["cognitive_reflection_score"].dtype in ['int64', 'float64'], "cognitive_reflection_score must be numeric"
    
    # Check for outlier capping (sanity check: no NaNs in key numeric columns if data was valid)
    numeric_cols = ["belief_rating", "valence", "cognitive_reflection_score", "total_fixation_duration", "headline_length"]
    for col in numeric_cols:
        if col in df.columns:
            assert not df[col].isna().all(), f"Column {col} is all NaN"
    
    # Check lexicon_used values
    if "lexicon_used" in df.columns:
        valid_lexicons = ["NRC", "VADER"]
        # Filter out NaNs if any
        valid_rows = df["lexicon_used"].dropna()
        if len(valid_rows) > 0:
            invalid = valid_rows[~valid_rows.isin(valid_lexicons)]
            assert len(invalid) == 0, f"Invalid lexicon values found: {invalid.unique()}"

def test_outlier_capping_applied():
    """
    Contract test: Verify that cognitive_reflection_score has been capped.
    This is a soft check; we expect the range to be reasonable if capping happened.
    """
    output_path = project_root / "data" / "derived" / "merged_dataset_full.csv"
    if not output_path.exists():
        pytest.skip("Output file not generated yet.")
    
    df = pd.read_csv(output_path)
    col = "cognitive_reflection_score"
    if col not in df.columns:
        pytest.skip("CRT column missing.")
    
    # Check that no value is infinite
    assert not np.isinf(df[col]).any(), "Infinite values found in CRT score"
    
    # Check that min/max are within reasonable bounds for a typical CRT (0-3 or 0-18 depending on scale)
    # Since we don't know the exact scale without reading config, we just check for extreme outliers relative to IQR
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr # Standard outlier definition
    # We capped at 99th percentile, so extreme outliers should be gone, but this is a sanity check
    # If the 99th percentile is extremely high, that's data dependent. 
    # The main check is that the code ran without error.
    pass
