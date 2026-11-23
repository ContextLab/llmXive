import os
import pandas as pd
import pytest
from pathlib import Path

def test_exclusion_log_exists():
    """Test that the exclusion log is created."""
    log_path = Path("data/interim/exclusion_log.csv")
    assert log_path.exists(), f"Exclusion log not found at {log_path}"

def test_exclusion_log_schema():
    """Test that the exclusion log has the correct schema."""
    log_path = Path("data/interin/exclusion_log.csv")
    if not log_path.exists():
        pytest.skip("Exclusion log not found, skipping schema test")
    
    df = pd.read_csv(log_path)
    required_columns = ["participant_id", "reason", "channels_rejected_ratio"]
    
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check reason values
    valid_reasons = ["high_variance", "ica_failure", "short_epoch"]
    if len(df) > 0:
        assert all(df["reason"].isin(valid_reasons)), f"Invalid reason values found: {df['reason'].unique()}"

def test_preprocessed_files_exist():
    """Test that preprocessed files are created."""
    output_dir = Path("data/interim/preprocessed_eeg")
    assert output_dir.exists(), f"Output directory not found: {output_dir}"
    
    fif_files = list(output_dir.glob("*.fif"))
    assert len(fif_files) > 0, "No preprocessed .fif files found"

def test_ica_cleaned_files_exist():
    """Test that ICA cleaned files are created."""
    output_dir = Path("data/interim/ica_cleaned_eeg")
    assert output_dir.exists(), f"Output directory not found: {output_dir}"
    
    fif_files = list(output_dir.glob("*.fif"))
    assert len(fif_files) > 0, "No ICA cleaned .fif files found"