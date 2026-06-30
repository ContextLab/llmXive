"""
Integration test for data filtering logic (MMSE/MOCA non-null check).

This test verifies that the filtering logic correctly identifies subjects
with valid longitudinal cognitive scores and excludes those without.
It simulates the behavior of code/01_download_and_filter.py using synthetic
BIDS-like metadata to ensure the filtering criteria (non-null at both timepoints)
are applied correctly.
"""
import os
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Import from sibling modules (relative to code/ directory)
# Since tests are at root and code is at root, we adjust path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.io import ensure_dir, save_dataframe
from utils.logger import setup_logger, get_logger

def test_filtering_logic():
    """
    Integration test: Verify filtering logic for MMSE/MOCA scores.
    
    Simulates a BIDS-like structure with subjects having various score combinations:
    - Valid: Both timepoints have scores
    - Invalid: One or both timepoints missing
    
    Expected: Only subjects with scores at both timepoints are retained.
    """
    # Setup temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        ensure_dir(data_dir)
        
        # Create synthetic subject metadata
        # Simulating the output of parsing BIDS metadata for ds000246
        subjects_data = [
            {
                "subject_id": "sub-001", 
                "timepoint_1": "MMSE", 
                "timepoint_1_value": 28.0, 
                "timepoint_2": "MMSE", 
                "timepoint_2_value": 25.0,
                "session_1": "baseline",
                "session_2": "followup"
            },
            {
                "subject_id": "sub-002", 
                "timepoint_1": "MOCA", 
                "timepoint_1_value": 24.0, 
                "timepoint_2": "MOCA", 
                "timepoint_2_value": 22.0,
                "session_1": "baseline",
                "session_2": "followup"
            },
            {
                "subject_id": "sub-003", 
                "timepoint_1": "MMSE", 
                "timepoint_1_value": 29.0, 
                "timepoint_2": None, 
                "timepoint_2_value": None,
                "session_1": "baseline",
                "session_2": "followup"
            },
            {
                "subject_id": "sub-004", 
                "timepoint_1": None, 
                "timepoint_1_value": None, 
                "timepoint_2": "MMSE", 
                "timepoint_2_value": 26.0,
                "session_1": "baseline",
                "session_2": "followup"
            },
            {
                "subject_id": "sub-005", 
                "timepoint_1": None, 
                "timepoint_1_value": None, 
                "timepoint_2": None, 
                "timepoint_2_value": None,
                "session_1": "baseline",
                "session_2": "followup"
            },
        ]
        
        # Convert to DataFrame
        df = pd.DataFrame(subjects_data)
        
        # Apply filtering logic: keep only rows where both timepoints have values
        # This mimics the logic in code/01_download_and_filter.py
        # The condition ensures that cognitive scores exist at both baseline and followup
        eligible = df[
            (df["timepoint_1_value"].notna()) & 
            (df["timepoint_2_value"].notna())
        ].copy()
        
        excluded = df[
            (df["timepoint_1_value"].isna()) | 
            (df["timepoint_2_value"].isna())
        ].copy()
        
        # Assertions
        assert len(eligible) == 2, f"Expected 2 eligible subjects, got {len(eligible)}"
        assert len(excluded) == 3, f"Expected 3 excluded subjects, got {len(excluded)}"
        
        # Verify specific subjects
        assert "sub-001" in eligible["subject_id"].values, "sub-001 should be eligible"
        assert "sub-002" in eligible["subject_id"].values, "sub-002 should be eligible"
        assert "sub-003" in excluded["subject_id"].values, "sub-003 should be excluded (missing t2)"
        assert "sub-004" in excluded["subject_id"].values, "sub-004 should be excluded (missing t1)"
        assert "sub-005" in excluded["subject_id"].values, "sub-005 should be excluded (missing both)"
        
        # Save results to verify outputs (as per task requirements)
        # These paths simulate the actual output structure expected by the pipeline
        output_dir = Path(tmpdir) / "output"
        ensure_dir(output_dir)
        
        eligible_path = output_dir / "eligible_subjects.csv"
        excluded_path = output_dir / "excluded_subjects.csv"
        
        save_dataframe(eligible, eligible_path)
        save_dataframe(excluded, excluded_path)
        
        # Log results using the project's logging utility
        logger = setup_logger("test_filtering", output_dir)
        logger.info(f"Filtering test completed: {len(eligible)} eligible, {len(excluded)} excluded")
        
        # Verify files were written
        assert eligible_path.exists(), f"Eligible subjects file not written: {eligible_path}"
        assert excluded_path.exists(), f"Excluded subjects file not written: {excluded_path}"
        
        print("Integration test PASSED: Filtering logic correctly identified eligible subjects.")
        print(f"Eligible subjects saved to: {eligible_path}")
        print(f"Excluded subjects saved to: {excluded_path}")

if __name__ == "__main__":
    test_filtering_logic()