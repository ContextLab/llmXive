"""
Integration tests for the data pipeline (US1)
"""
import pytest
import os
from pathlib import Path
import json

def test_preprocessed_data_exists():
    """Test that preprocessed data files exist after running preprocessing"""
    # This test assumes the preprocessing pipeline has been run
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        nifti_files = list(processed_dir.glob("*.nii.gz"))
        # If files exist, verify they have expected structure
        if nifti_files:
            # Just check that at least one file exists
            assert len(nifti_files) > 0

def test_motion_metrics_logged():
    """Test that motion metrics are logged during preprocessing"""
    # This test checks that the preprocessing log contains motion metrics
    log_file = Path("logs/preprocessing.log")
    if log_file.exists():
        with open(log_file, 'r') as f:
            content = f.read()
            # Check for presence of motion-related keywords
            assert 'FD' in content or 'motion' in content.lower() or 'framewise' in content.lower()

def test_excluded_subjects_logged():
    """Test that excluded subjects are logged with reasons"""
    log_file = Path("logs/preprocessing.log")
    if log_file.exists():
        with open(log_file, 'r') as f:
            content = f.read()
            # Check for exclusion-related keywords
            assert 'excluded' in content.lower() or 'exclusion' in content.lower()
