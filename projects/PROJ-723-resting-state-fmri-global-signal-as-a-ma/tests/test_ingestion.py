"""
Unit tests for ingestion.py focusing on exclusion logic.

Tests cover:
1. Missing pairs (subjects present in fMRI but not MWQ, and vice versa).
2. High motion exclusion (Mean_FD > 0.5mm).
3. Zero variance exclusion (Global_Signal_SD == 0).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import (
    join_fmri_mwq_data,
    apply_motion_exclusion,
    check_zero_variance_subjects
)

# --- Fixtures ---

@pytest.fixture
def sample_fmri_data():
    """Create a mock fMRI dataset with various motion levels and IDs."""
    data = {
        'Subject_ID': ['sub-001', 'sub-002', 'sub-003', 'sub-004', 'sub-005'],
        'global_signal_sd': [0.5, 0.6, 0.4, 0.0, 0.7],  # sub-004 has zero variance
        'Mean_FD': [0.2, 0.8, 0.3, 0.4, 0.9],          # sub-002, sub-005 are high motion
        'Mean_DVARS': [1.5, 2.0, 1.2, 1.8, 2.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_mwq_data():
    """Create a mock MWQ dataset. Note: sub-003 is missing (simulating missing pair)."""
    data = {
        'Subject_ID': ['sub-001', 'sub-002', 'sub-004', 'sub-005'],
        'MWQ_Score': [15, 22, 18, 30],
        'Age': [25, 30, 28, 35],
        'Sex': ['M', 'F', 'M', 'F']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_cleaned_data():
    """Data already joined, ready for motion/zero-variance checks."""
    data = {
        'Subject_ID': ['sub-001', 'sub-002', 'sub-003', 'sub-004', 'sub-005'],
        'Global_Signal_SD': [0.5, 0.6, 0.4, 0.0, 0.7],
        'MWQ_Score': [15, 22, 18, 18, 30],
        'Age': [25, 30, 28, 28, 35],
        'Sex': ['M', 'F', 'M', 'M', 'F'],
        'Mean_FD': [0.2, 0.8, 0.3, 0.4, 0.9],
        'Mean_DVARS': [1.5, 2.0, 1.2, 1.8, 2.5]
    }
    return pd.DataFrame(data)

# --- Tests: Missing Pairs (Join Logic) ---

def test_join_fmri_mwq_data_excludes_missing_pairs(sample_fmri_data, sample_mwq_data):
    """
    Verify that join_fmri_mwq_data correctly excludes subjects that do not appear
    in both datasets (inner join behavior).
    """
    # Expected: sub-003 is in FMRI but not MWQ -> Excluded
    # Expected: All others (001, 002, 004, 005) are in both -> Included
    
    result = join_fmri_mwq_data(sample_fmri_data, sample_mwq_data)
    
    # Check counts
    assert len(result) == 4, f"Expected 4 subjects after join, got {len(result)}"
    
    # Check specific IDs
    assert 'sub-003' not in result['Subject_ID'].values, "sub-003 should be excluded (missing MWQ data)"
    assert set(result['Subject_ID'].values) == {'sub-001', 'sub-002', 'sub-004', 'sub-005'}
    
    # Verify data integrity for a known subject
    sub001_row = result[result['Subject_ID'] == 'sub-001'].iloc[0]
    assert sub001_row['global_signal_sd'] == 0.5
    assert sub001_row['MWQ_Score'] == 15

# --- Tests: High Motion Exclusion ---

def test_apply_motion_exclusion_removes_high_fd(sample_cleaned_data, caplog):
    """
    Verify that apply_motion_exclusion removes subjects with Mean_FD > 0.5.
    Also verifies that exclusion counts/IDs are logged.
    """
    # Threshold is 0.5
    # sub-002 (0.8) and sub-005 (0.9) should be removed
    # sub-001 (0.2), sub-003 (0.3), sub-004 (0.4) should remain
    
    result = apply_motion_exclusion(sample_cleaned_data, threshold=0.5)
    
    # Check counts
    assert len(result) == 3, f"Expected 3 subjects after motion exclusion, got {len(result)}"
    
    # Check specific IDs
    excluded_ids = result[result['Mean_FD'] > 0.5]['Subject_ID'].tolist()
    assert len(excluded_ids) == 0, "No high motion subjects should remain in result"
    
    remaining_ids = set(result['Subject_ID'].tolist())
    assert remaining_ids == {'sub-001', 'sub-003', 'sub-004'}
    
    # Verify logging (caplog captures log output)
    assert "excluded" in caplog.text.lower() or "motion" in caplog.text.lower(), \
        "Exclusion logic should log the exclusion event."
    
    # Verify specific subject IDs were mentioned in logs if possible (depending on impl)
    # We rely on the function's return value being correct primarily.

def test_apply_motion_exclusion_threshold_boundary(sample_cleaned_data):
    """
    Verify boundary condition: FD exactly equal to threshold is kept, > threshold is removed.
    """
    # Add a subject with exactly 0.5 FD
    boundary_data = sample_cleaned_data.copy()
    new_row = pd.DataFrame([{
        'Subject_ID': 'sub-006',
        'Global_Signal_SD': 0.5,
        'MWQ_Score': 20,
        'Age': 25,
        'Sex': 'M',
        'Mean_FD': 0.5,
        'Mean_DVARS': 1.5
    }])
    boundary_data = pd.concat([boundary_data, new_row], ignore_index=True)
    
    result = apply_motion_exclusion(boundary_data, threshold=0.5)
    
    # sub-006 (0.5) should be KEPT
    assert 'sub-006' in result['Subject_ID'].values, "Subject with FD == 0.5 should be kept"
    
    # sub-002 (0.8) and sub-005 (0.9) should be REMOVED
    assert 'sub-002' not in result['Subject_ID'].values
    assert 'sub-005' not in result['Subject_ID'].values

# --- Tests: Zero Variance Exclusion ---

def test_check_zero_variance_excludes_zero_sd(sample_cleaned_data, caplog):
    """
    Verify that check_zero_variance_subjects removes subjects with Global_Signal_SD == 0.
    """
    # sub-004 has 0.0 SD
    result, excluded_ids = check_zero_variance_subjects(sample_cleaned_data)
    
    # Check result
    assert len(result) == 4, f"Expected 4 subjects after zero-variance check, got {len(result)}"
    assert 'sub-004' not in result['Subject_ID'].values, "sub-004 should be excluded"
    
    # Check return value for excluded IDs
    assert 'sub-004' in excluded_ids, "Function should return list of excluded IDs"
    
    # Check logging
    assert "zero variance" in caplog.text.lower() or "excluded" in caplog.text.lower(), \
        "Zero variance exclusion should be logged"

def test_check_zero_variance_no_false_positives(sample_cleaned_data):
    """
    Verify that subjects with non-zero SD are NOT excluded.
    """
    # All except sub-004 have non-zero SD
    result, excluded_ids = check_zero_variance_subjects(sample_cleaned_data)
    
    expected_kept = {'sub-001', 'sub-002', 'sub-003', 'sub-005'}
    assert set(result['Subject_ID'].tolist()) == expected_kept
    assert len(excluded_ids) == 1
    assert excluded_ids[0] == 'sub-004'

# --- Integration Test: Combined Exclusion Logic ---

def test_combined_exclusion_pipeline(sample_fmri_data, sample_mwq_data, caplog):
    """
    Simulate the full pipeline: Join -> Motion Exclusion -> Zero Variance.
    Ensure final dataset contains only valid subjects.
    """
    # 1. Join
    joined = join_fmri_mwq_data(sample_fmri_data, sample_mwq_data)
    # Expected: sub-003 removed. Kept: 001, 002, 004, 005.
    assert len(joined) == 4
    
    # 2. Motion Exclusion (threshold 0.5)
    # sub-002 (0.8), sub-005 (0.9) removed. Kept: 001, 004.
    motion_filtered = apply_motion_exclusion(joined, threshold=0.5)
    assert len(motion_filtered) == 2
    assert set(motion_filtered['Subject_ID'].tolist()) == {'sub-001', 'sub-004'}
    
    # 3. Zero Variance
    # sub-004 (0.0) removed. Kept: 001.
    final_data, excluded_zv = check_zero_variance_subjects(motion_filtered)
    assert len(final_data) == 1
    assert final_data.iloc[0]['Subject_ID'] == 'sub-001'
    assert 'sub-004' in excluded_zv

    # Verify logs captured
    assert "excluded" in caplog.text.lower()
    assert "motion" in caplog.text.lower()
    assert "zero variance" in caplog.text.lower()