"""
Tests for T017 Exclusion Logic.
"""
import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock dependencies for testing
import unittest.mock as mock

from exclusion_tracker import ensure_exclusions_file_exists, log_exclusion, get_excluded_subjects
from exclusion_logic import run_exclusion_check, MIN_TRIALS_PER_CONDITION, MAX_ARTIFACT_REMOVAL_RATIO

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    os.makedirs(os.path.join(temp, "data"), exist_ok=True)
    os.makedirs(os.path.join(temp, "logs"), exist_ok=True)
    # Set environment or mock paths
    yield temp
    shutil.rmtree(temp)

def test_exclusion_insufficient_trials(temp_dir):
    """Test exclusion for insufficient trials."""
    # Mock the log_exclusion to verify it's called
    with mock.patch('exclusion_tracker.log_exclusion') as mock_log:
        result = run_exclusion_check("sub-01", min_trials=5, artifact_ratio=0.1)
        
        assert result is not None
        assert result["reason"] == "insufficient_trials"
        assert result["subject_id"] == "sub-01"
        mock_log.assert_called_once_with("sub-01", "insufficient_trials")

def test_exclusion_excessive_artifact(temp_dir):
    """Test exclusion for excessive artifact removal."""
    with mock.patch('exclusion_tracker.log_exclusion') as mock_log:
        result = run_exclusion_check("sub-02", min_trials=15, artifact_ratio=0.6)
        
        assert result is not None
        assert result["reason"] == "excessive_artifact_removal"
        assert result["subject_id"] == "sub-02"
        mock_log.assert_called_once_with("sub-02", "excessive_artifact_removal")

def test_no_exclusion(temp_dir):
    """Test that a valid subject is not excluded."""
    with mock.patch('exclusion_tracker.log_exclusion') as mock_log:
        result = run_exclusion_check("sub-03", min_trials=15, artifact_ratio=0.1)
        
        assert result is None
        mock_log.assert_not_called()

def test_boundary_conditions(temp_dir):
    """Test boundary conditions."""
    # Exactly 10 trials should pass
    with mock.patch('exclusion_tracker.log_exclusion') as mock_log:
        result = run_exclusion_check("sub-04", min_trials=10, artifact_ratio=0.1)
        assert result is None
        
        # Exactly 50% removal should pass (strictly greater than 50% triggers)
        result = run_exclusion_check("sub-05", min_trials=15, artifact_ratio=0.5)
        assert result is None
        
        # 50.1% removal should fail
        result = run_exclusion_check("sub-06", min_trials=15, artifact_ratio=0.501)
        assert result is not None
        assert result["reason"] == "excessive_artifact_removal"
