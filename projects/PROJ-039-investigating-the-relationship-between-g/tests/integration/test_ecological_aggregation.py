"""
Integration test for Ecological Aggregation success (US1).

Verifies:
1. data/processed/microbiome_features.csv exists and has >= 100 rows.
2. data/processed/eeg_features.csv exists and has >= 50 subjects.
3. data/processed/stratum_features.csv exists and contains valid strata.
4. artifacts/strata_report.json exists and contains valid_strata_count >= 5.

This test assumes T014 (ecological_aggregation.py) and T015 (compute_stratum_means.py)
have been executed successfully.
"""
import os
import json
import pandas as pd
import pytest
from pathlib import Path

# Import project utilities to ensure path resolution matches project structure
from config import get_project_root

PROJECT_ROOT = get_project_root()
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
ARTIFACTS = PROJECT_ROOT / "artifacts"

def test_microbiome_data_exists_and_sufficient():
    """Verify microbiome features file exists and has >= 100 rows."""
    file_path = DATA_PROCESSED / "microbiome_features.csv"
    assert file_path.exists(), f"Microbiome features file not found: {file_path}"
    
    df = pd.read_csv(file_path)
    assert len(df) >= 100, f"Microbiome features has {len(df)} rows, expected >= 100"

def test_eeg_data_exists_and_sufficient():
    """Verify EEG features file exists and has >= 50 subjects."""
    file_path = DATA_PROCESSED / "eeg_features.csv"
    assert file_path.exists(), f"EEG features file not found: {file_path}"
    
    df = pd.read_csv(file_path)
    # Assuming each row is a subject (or unique subject ID)
    # If the file has multiple rows per subject, we should count unique IDs.
    # Based on typical preprocessing outputs, we check unique subject IDs or row count.
    if 'subject_id' in df.columns:
        unique_subjects = df['subject_id'].nunique()
    else:
        unique_subjects = len(df)
        
    assert unique_subjects >= 50, f"EEG features has {unique_subjects} subjects, expected >= 50"

def test_stratum_features_exists():
    """Verify stratum features file exists."""
    file_path = DATA_PROCESSED / "stratum_features.csv"
    assert file_path.exists(), f"Stratum features file not found: {file_path}"
    
    df = pd.read_csv(file_path)
    assert len(df) > 0, "Stratum features file is empty"
    
    # Verify expected columns exist
    required_columns = ['stratum_id', 'mean_alpha_power', 'clr_taxa_abundances', 'n_subjects']
    for col in required_columns:
        assert col in df.columns, f"Missing required column in stratum_features.csv: {col}"

def test_strata_report_valid_strata_count():
    """Verify strata report exists and valid_strata_count >= 5."""
    file_path = ARTIFACTS / "strata_report.json"
    assert file_path.exists(), f"Strata report file not found: {file_path}"
    
    with open(file_path, 'r') as f:
        report = json.load(f)
    
    assert 'valid_strata_count' in report, "Missing 'valid_strata_count' in strata_report.json"
    
    count = report['valid_strata_count']
    assert isinstance(count, int), f"valid_strata_count should be an integer, got {type(count)}"
    assert count >= 5, f"valid_strata_count is {count}, but must be >= 5 for ecological analysis to proceed"

def test_strata_consistency():
    """Verify consistency between stratum_features.csv and strata_report.json."""
    stratum_file = DATA_PROCESSED / "stratum_features.csv"
    report_file = ARTIFACTS / "strata_report.json"
    
    assert stratum_file.exists() and report_file.exists()
    
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    df = pd.read_csv(stratum_file)
    
    # The number of rows in stratum_features should match valid_strata_count
    # (assuming only valid strata are written to the final features file)
    reported_count = report['valid_strata_count']
    actual_count = len(df)
    
    assert actual_count == reported_count, (
        f"Mismatch: stratum_features.csv has {actual_count} rows, "
        f"but strata_report.json reports {reported_count} valid strata"
    )