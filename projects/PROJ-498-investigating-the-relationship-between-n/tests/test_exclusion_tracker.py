import pytest
import os
import csv
from pathlib import Path
from exclusion_tracker import (
    ensure_exclusions_file_exists,
    log_exclusion,
    evaluate_subject_for_exclusion,
    get_excluded_subjects,
    EXCLUSIONS_FILE
)

@pytest.fixture
def clean_exclusions_file():
    # Ensure file is removed before test
    if os.path.exists(EXCLUSIONS_FILE):
        os.remove(EXCLUSIONS_FILE)
    yield
    # Cleanup after test
    if os.path.exists(EXCLUSIONS_FILE):
        os.remove(EXCLUSIONS_FILE)

def test_ensure_exclusions_file_exists(clean_exclusions_file):
    ensure_exclusions_file_exists()
    assert os.path.exists(EXCLUSIONS_FILE)
    with open(EXCLUSIONS_FILE, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['subject_id', 'reason']

def test_log_exclusion(clean_exclusions_file):
    log_exclusion("sub-001", "insufficient trials")
    assert os.path.exists(EXCLUSIONS_FILE)
    
    excluded = get_excluded_subjects()
    assert len(excluded) == 1
    assert excluded[0] == ("sub-001", "insufficient trials")

def test_evaluate_subject_insufficient_trials():
    # Test < 10 trials in one condition
    trials = {"switch": 5, "stay": 15}
    reason = evaluate_subject_for_exclusion("sub-001", trials, 20)
    assert reason == "insufficient trials"

def test_evaluate_subject_excessive_artifact():
    # Test > 50% artifact removal
    # Initial = 100, Final = 40 -> Removed 60 (60%)
    trials = {"switch": 20, "stay": 20} # Total 40
    reason = evaluate_subject_for_exclusion("sub-002", trials, 100)
    assert reason == "excessive artifact removal"

def test_evaluate_subject_pass():
    # Test passing both criteria
    trials = {"switch": 15, "stay": 15} # Total 30
    # Initial 40, Removed 10 (25%) -> OK
    reason = evaluate_subject_for_exclusion("sub-003", trials, 40)
    assert reason is None

def test_multiple_exclusions(clean_exclusions_file):
    log_exclusion("sub-001", "insufficient trials")
    log_exclusion("sub-002", "excessive artifact removal")
    
    excluded = get_excluded_subjects()
    assert len(excluded) == 2
    assert ("sub-001", "insufficient trials") in excluded
    assert ("sub-002", "excessive artifact removal") in excluded
