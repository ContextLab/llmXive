"""
Unit tests for participant assignment logic (T014b).
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root / 'code'))

from experiment.assignment import (
    stratified_random_assignment,
    load_participant_list,
    save_assignment_log,
    CONDITIONS
)


@pytest.fixture
def sample_participants():
    """Create a sample list of participants."""
    return [
        {'participant_id': 'P001', 'age': 25, 'role': 'developer'},
        {'participant_id': 'P002', 'age': 30, 'role': 'manager'},
        {'participant_id': 'P003', 'age': 28, 'role': 'developer'},
        {'participant_id': 'P004', 'age': 35, 'role': 'analyst'},
        {'participant_id': 'P005', 'age': 22, 'role': 'intern'},
        {'participant_id': 'P006', 'age': 29, 'role': 'developer'},
    ]


@pytest.fixture
def temp_participant_file(sample_participants):
    """Create a temporary file with participant data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'participants': sample_participants}, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_stratified_assignment_balance(sample_participants):
    """Test that assignment is balanced across conditions."""
    n = len(sample_participants)
    k = len(CONDITIONS)
    perfect = n // k
    remainder = n % k

    # Run assignment multiple times to ensure consistency
    for _ in range(10):
        assignment = stratified_random_assignment(sample_participants, seed=42)

        # Count assignments per condition
        counts = {cond: 0 for cond in CONDITIONS}
        for cond in assignment.values():
            counts[cond] += 1

        # Verify balance: each condition should have perfect or perfect+1
        for cond, count in counts.items():
            assert count == perfect or count == perfect + 1, \
                f"Condition {cond} has {count} assignments, expected {perfect} or {perfect+1}"

        # Verify all participants are assigned
        assert len(assignment) == n


def test_stratified_assignment_coverage(sample_participants):
    """Test that all conditions are represented."""
    assignment = stratified_random_assignment(sample_participants, seed=42)
    assigned_conditions = set(assignment.values())

    # All conditions should be used
    assert assigned_conditions == set(CONDITIONS)


def test_assignment_uniqueness(sample_participants):
    """Test that each participant is assigned exactly once."""
    assignment = stratified_random_assignment(sample_participants, seed=42)

    participant_ids = [p['participant_id'] for p in sample_participants]
    assert set(assignment.keys()) == set(participant_ids)
    assert len(assignment) == len(participant_ids)


def test_load_participant_list(temp_participant_file):
    """Test loading participant list from file."""
    participants = load_participant_list(temp_participant_file)
    assert len(participants) == 6
    assert participants[0]['participant_id'] == 'P001'


def test_load_participant_list_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_participant_list('nonexistent_file.json')


def test_save_assignment_log(sample_participants):
    """Test saving assignment log to file."""
    assignment = stratified_random_assignment(sample_participants, seed=42)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        save_assignment_log(assignment, temp_path)
        assert os.path.exists(temp_path)

        with open(temp_path, 'r') as f:
            saved_data = json.load(f)

        assert 'assignments' in saved_data
        assert 'metadata' in saved_data
        assert len(saved_data['assignments']) == len(sample_participants)
    finally:
        os.unlink(temp_path)


def test_empty_participant_list():
    """Test error handling for empty participant list."""
    with pytest.raises(ValueError):
        stratified_random_assignment([])


def test_missing_participant_id(sample_participants):
    """Test error handling for missing participant_id."""
    invalid_participants = sample_participants.copy()
    invalid_participants[0] = {'age': 25}  # Missing participant_id

    with pytest.raises(ValueError):
        stratified_random_assignment(invalid_participants)