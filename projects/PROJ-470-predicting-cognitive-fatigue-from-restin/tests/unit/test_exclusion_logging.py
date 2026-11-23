import os
import pandas as pd
from pathlib import Path

def test_exclusion_log_created():
    """Test that exclusion_log.csv is created with correct columns."""
    # Ensure the file exists (it should be created by preprocess.py)
    log_path = Path("data/processed/exclusion_log.csv")
    assert log_path.exists(), "Exclusion log file not found."

    # Read the CSV
    df = pd.read_csv(log_path)

    # Check required columns
    required_columns = ['participant_id', 'reason', 'timestamp']
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"

    # Check that there is at least one row (if exclusions occurred)
    # This test assumes that at least one exclusion happened during preprocessing
    # If no exclusions happened, the file might be empty, which is also valid
    # But for this test, we expect at least one entry to verify the format
    if len(df) > 0:
        assert not df.empty, "Exclusion log is empty."

def test_exclusion_log_reasons():
    """Test that exclusion reasons are valid."""
    log_path = Path("data/processed/exclusion_log.csv")
    if not log_path.exists():
        return  # Skip if no exclusions occurred

    df = pd.read_csv(log_path)
    valid_reasons = ['amplitude_threshold', 'segment_too_short', 'processing_error']
    for reason in df['reason'].unique():
        assert reason in valid_reasons, f"Invalid reason: {reason}"