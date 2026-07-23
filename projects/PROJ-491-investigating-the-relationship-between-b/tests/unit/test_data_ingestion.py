"""
Unit tests for session ID validation logic in data ingestion.

This module tests the logic that validates session IDs to ensure
distinctness and prevent double-dipping in the downstream pipeline.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the logic to test. Since data_ingestion.py is not yet fully implemented,
# we define the validation logic here to be tested, or we assume it will be
# imported from code/data_ingestion.py once implemented.
# For now, we implement the validation function here to ensure tests can run
# against the logic, and the final implementation in code/data_ingestion.py
# will call this same logic.

def validate_session_ids(subject_sessions: dict) -> tuple:
    """
    Validate session IDs for distinctness.

    Args:
        subject_sessions: A dictionary mapping subject IDs to their session IDs.
                         Example: {'sub-001': 'ses-01', 'sub-002': 'ses-01'}

    Returns:
        A tuple (valid_subjects, excluded_subjects, pass_rate) where:
        - valid_subjects: List of subject IDs with distinct session IDs
        - excluded_subjects: List of subject IDs excluded due to session ID mismatch
        - pass_rate: Percentage of subjects with distinct session IDs
    """
    if not subject_sessions:
        return [], [], 0.0

    # Count occurrences of each session ID
    session_counts = {}
    for sub_id, ses_id in subject_sessions.items():
        session_counts[ses_id] = session_counts.get(ses_id, 0) + 1

    # Identify sessions that appear more than once
    duplicate_sessions = {ses for ses, count in session_counts.items() if count > 1}

    valid_subjects = []
    excluded_subjects = []

    for sub_id, ses_id in subject_sessions.items():
        if ses_id in duplicate_sessions:
            excluded_subjects.append(sub_id)
        else:
            valid_subjects.append(sub_id)

    total_subjects = len(subject_sessions)
    pass_rate = (len(valid_subjects) / total_subjects * 100) if total_subjects > 0 else 0.0

    return valid_subjects, excluded_subjects, pass_rate


class TestSessionIdValidation:
    """Tests for the session ID validation logic."""

    def test_all_distinct_sessions(self):
        """Test when all subjects have distinct session IDs."""
        subject_sessions = {
            'sub-001': 'ses-01',
            'sub-002': 'ses-02',
            'sub-003': 'ses-03'
        }
        valid, excluded, pass_rate = validate_session_ids(subject_sessions)

        assert len(valid) == 3
        assert len(excluded) == 0
        assert pass_rate == 100.0
        assert excluded == []

    def test_all_duplicate_sessions(self):
        """Test when all subjects share the same session ID."""
        subject_sessions = {
            'sub-001': 'ses-01',
            'sub-002': 'ses-01',
            'sub-003': 'ses-01'
        }
        valid, excluded, pass_rate = validate_session_ids(subject_sessions)

        assert len(valid) == 0
        assert len(excluded) == 3
        assert pass_rate == 0.0

    def test_mixed_distinct_and_duplicate(self):
        """Test when some subjects have distinct sessions and others share."""
        subject_sessions = {
            'sub-001': 'ses-01',
            'sub-002': 'ses-01',
            'sub-003': 'ses-02',
            'sub-004': 'ses-03'
        }
        valid, excluded, pass_rate = validate_session_ids(subject_sessions)

        assert len(valid) == 2  # sub-003 and sub-004
        assert len(excluded) == 2  # sub-001 and sub-002
        assert pass_rate == 50.0
        assert 'sub-003' in valid
        assert 'sub-004' in valid
        assert 'sub-001' in excluded
        assert 'sub-002' in excluded

    def test_empty_input(self):
        """Test with empty subject_sessions dictionary."""
        valid, excluded, pass_rate = validate_session_ids({})

        assert len(valid) == 0
        assert len(excluded) == 0
        assert pass_rate == 0.0

    def test_single_subject(self):
        """Test with a single subject."""
        subject_sessions = {'sub-001': 'ses-01'}
        valid, excluded, pass_rate = validate_session_ids(subject_sessions)

        assert len(valid) == 1
        assert len(excluded) == 0
        assert pass_rate == 100.0

    def test_pass_rate_calculation(self):
        """Test pass rate calculation with known values."""
        subject_sessions = {
            'sub-001': 'ses-01',
            'sub-002': 'ses-01',
            'sub-003': 'ses-01',
            'sub-004': 'ses-02',
            'sub-005': 'ses-02',
            'sub-006': 'ses-03',
            'sub-007': 'ses-04',
            'sub-008': 'ses-05'
        }
        # ses-01 (2), ses-02 (2) are duplicates -> excluded: sub-001, sub-002, sub-003, sub-004
        # ses-03, ses-04, ses-05 are unique -> valid: sub-006, sub-007, sub-008
        valid, excluded, pass_rate = validate_session_ids(subject_sessions)

        assert len(valid) == 3
        assert len(excluded) == 5
        assert pass_rate == 37.5  # 3/8 * 100

    def test_three_way_duplicate(self):
        """Test with a session ID shared by three subjects."""
        subject_sessions = {
            'sub-001': 'ses-01',
            'sub-002': 'ses-01',
            'sub-003': 'ses-01',
            'sub-004': 'ses-02'
        }
        valid, excluded, pass_rate = validate_session_ids(subject_sessions)

        assert len(valid) == 1
        assert len(excluded) == 3
        assert pass_rate == 25.0
        assert 'sub-004' in valid
        assert 'sub-001' in excluded
        assert 'sub-002' in excluded
        assert 'sub-003' in excluded