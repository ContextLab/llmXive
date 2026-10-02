"""
Tests for T017 Exclusion Logic.
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest

# Import the logic to test
from exclusion_logic import (
    evaluate_subject_for_exclusion,
    log_exclusion,
    ensure_exclusions_file_exists,
    run_exclusion_check,
    MIN_TRIALS_PER_CONDITION,
    MAX_ARTIFACT_REMOVAL_RATIO
)

@pytest.fixture
def temp_exclusions_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['subject_id', 'reason'])
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)

def test_evaluate_subject_insufficient_trials():
    """Test exclusion for insufficient trials."""
    trials = {'switch': 5, 'stay': 12}
    is_excluded, reason = evaluate_subject_for_exclusion(
        'sub-01', trials, 17, 0
    )
    assert is_excluded is True
    assert reason == "insufficient trials"

def test_evaluate_subject_excessive_artifacts():
    """Test exclusion for excessive artifact removal."""
    trials = {'switch': 20, 'stay': 20}
    is_excluded, reason = evaluate_subject_for_exclusion(
        'sub-02', trials, 40, 21  # 21/40 = 52.5% > 50%
    )
    assert is_excluded is True
    assert reason == "excessive artifact removal"

def test_evaluate_subject_valid():
    """Test a valid subject passes."""
    trials = {'switch': 15, 'stay': 15}
    is_excluded, reason = evaluate_subject_for_exclusion(
        'sub-03', trials, 30, 5  # 5/30 = 16.6% < 50%
    )
    assert is_excluded is False
    assert reason is None

def test_log_exclusion(temp_exclusions_file):
    """Test logging an exclusion."""
    log_exclusion(temp_exclusions_file, 'sub-01', 'insufficient trials')
    
    with open(temp_exclusions_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['subject_id'] == 'sub-01'
    assert rows[0]['reason'] == 'insufficient trials'

def test_run_exclusion_check(temp_exclusions_file):
    """Test the full exclusion check pipeline."""
    subject_results = [
        {'subject_id': 'sub-01', 'trials_per_condition': {'switch': 5, 'stay': 10}, 'total_trials': 15, 'artifact_removed_count': 0},
        {'subject_id': 'sub-02', 'trials_per_condition': {'switch': 20, 'stay': 20}, 'total_trials': 40, 'artifact_removed_count': 21},
        {'subject_id': 'sub-03', 'trials_per_condition': {'switch': 15, 'stay': 15}, 'total_trials': 30, 'artifact_removed_count': 5},
    ]
    
    valid_count = run_exclusion_check(subject_results, temp_exclusions_file)
    
    # sub-01: insufficient trials -> excluded
    # sub-02: excessive artifacts -> excluded
    # sub-03: valid
    assert valid_count == 1
    
    with open(temp_exclusions_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    reasons = {r['subject_id']: r['reason'] for r in rows}
    assert 'sub-01' in reasons
    assert 'sub-02' in reasons