"""
Contract test for counterbalancing task (T014).

Verifies that:
1. Each participant has exactly 2 * N trials (N = number of stimuli)
2. Each stimulus appears exactly twice per participant (once per context)
3. Both relationship contexts are represented for every stimulus-participant pair
"""
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

import pytest

from config import get_processed_data_dir, get_raw_data_dir

# Constants
CONTEXTS = ["friend", "acquaintance"]


def load_counterbalanced_trials() -> List[Dict[str, Any]]:
    """Load counterbalanced trials from CSV."""
    trials_path = get_processed_data_dir() / "counterbalanced_trials.csv"
    
    if not trials_path.exists():
        pytest.fail(f"Counterbalanced trials file not found: {trials_path}")
    
    trials = []
    with open(trials_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['emoji_count'] = int(row['emoji_count'])
            row['length_category'] = int(row['length_category'])
            trials.append(row)
    
    return trials


def load_stimuli() -> List[Dict[str, Any]]:
    """Load stimuli from raw stimuli CSV."""
    stimuli_path = get_raw_data_dir() / "stimuli.csv"
    
    if not stimuli_path.exists():
        pytest.fail(f"Stimuli file not found: {stimuli_path}")
    
    stimuli = []
    with open(stimuli_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['emoji_count'] = int(row['emoji_count'])
            row['length_category'] = int(row['length_category'])
            stimuli.append(row)
    
    return stimuli


@pytest.fixture
def trials() -> List[Dict[str, Any]]:
    """Fixture to load counterbalanced trials."""
    return load_counterbalanced_trials()


@pytest.fixture
def stimuli() -> List[Dict[str, Any]]:
    """Fixture to load stimuli."""
    return load_stimuli()


@pytest.fixture
def stimulus_ids(stimuli) -> Set[str]:
    """Set of all stimulus IDs."""
    return {s['id'] for s in stimuli}


class TestCounterbalancing:
    """Test suite for counterbalancing contract."""

    def test_file_exists(self):
        """Test that counterbalanced trials file exists."""
        trials_path = get_processed_data_dir() / "counterbalanced_trials.csv"
        assert trials_path.exists(), "Counterbalanced trials file must exist"

    def test_non_empty(self, trials):
        """Test that counterbalanced trials file is not empty."""
        assert len(trials) > 0, "Counterbalanced trials must not be empty"

    def test_required_columns(self, trials):
        """Test that all required columns are present."""
        required_columns = {
            'participant_id', 'stimulus_id', 'stimulus_text',
            'relationship_context', 'emoji_count', 'punctuation_type',
            'length_category', 'scenario_id', 'cue_intensity'
        }
        
        if trials:
            actual_columns = set(trials[0].keys())
            missing = required_columns - actual_columns
            assert not missing, f"Missing required columns: {missing}"

    def test_each_participant_has_correct_trial_count(
        self, trials, stimuli
    ):
        """Test that each participant has exactly 2 * N trials."""
        expected_count = len(stimuli) * len(CONTEXTS)
        
        # Group by participant
        participant_counts: Dict[str, int] = {}
        for trial in trials:
            pid = trial['participant_id']
            participant_counts[pid] = participant_counts.get(pid, 0) + 1
        
        for pid, count in participant_counts.items():
            assert count == expected_count, (
                f"Participant {pid} has {count} trials, "
                f"expected {expected_count}"
            )

    def test_each_stimulus_appears_twice_per_participant(
        self, trials, stimulus_ids
    ):
        """Test that each stimulus appears exactly twice per participant."""
        # Group by participant
        participant_stimuli: Dict[str, Dict[str, int]] = {}
        
        for trial in trials:
            pid = trial['participant_id']
            sid = trial['stimulus_id']
            
            if pid not in participant_stimuli:
                participant_stimuli[pid] = {}
            
            participant_stimuli[pid][sid] = participant_stimuli[pid].get(sid, 0) + 1
        
        for pid, stimulus_counts in participant_stimuli.items():
            for sid, count in stimulus_counts.items():
                assert count == 2, (
                    f"Stimulus {sid} for participant {pid} appears {count} times, "
                    f"expected 2"
                )

    def test_both_contexts_for_each_stimulus_participant_pair(
        self, trials, stimulus_ids
    ):
        """Test that both contexts are present for each stimulus-participant pair."""
        # Group by participant
        participant_data: Dict[str, Dict[str, Set[str]]] = {}
        
        for trial in trials:
            pid = trial['participant_id']
            sid = trial['stimulus_id']
            ctx = trial['relationship_context']
            
            if pid not in participant_data:
                participant_data[pid] = {}
            
            if sid not in participant_data[pid]:
                participant_data[pid][sid] = set()
            
            participant_data[pid][sid].add(ctx)
        
        for pid, stimulus_contexts in participant_data.items():
            for sid, contexts in stimulus_contexts.items():
                assert contexts == set(CONTEXTS), (
                    f"Stimulus {sid} for participant {pid} has contexts {contexts}, "
                    f"expected {CONTEXTS}"
                )

    def test_all_stimuli_represented_for_each_participant(
        self, trials, stimulus_ids
    ):
        """Test that all stimuli are present for each participant."""
        # Group by participant
        participant_stimuli: Dict[str, Set[str]] = {}
        
        for trial in trials:
            pid = trial['participant_id']
            sid = trial['stimulus_id']
            
            if pid not in participant_stimuli:
                participant_stimuli[pid] = set()
            
            participant_stimuli[pid].add(sid)
        
        for pid, present_stimuli in participant_stimuli.items():
            assert present_stimuli == stimulus_ids, (
                f"Participant {pid} missing stimuli: {stimulus_ids - present_stimuli}"
            )

    def test_no_duplicate_stimulus_context_pairs(
        self, trials
    ):
        """Test that no stimulus-context pair is duplicated for a participant."""
        # Group by participant
        participant_pairs: Dict[str, Set[Tuple[str, str]]] = {}
        
        for trial in trials:
            pid = trial['participant_id']
            sid = trial['stimulus_id']
            ctx = trial['relationship_context']
            pair = (sid, ctx)
            
            if pid not in participant_pairs:
                participant_pairs[pid] = set()
            
            assert pair not in participant_pairs[pid], (
                f"Duplicate stimulus-context pair {pair} for participant {pid}"
            )
            participant_pairs[pid].add(pair)

    def test_total_trial_count_matches_expectation(
        self, trials, stimuli
    ):
        """Test that total trial count matches expected value."""
        # Get unique participants
        participants = set(t['participant_id'] for t in trials)
        expected_total = len(participants) * len(stimuli) * len(CONTEXTS)
        
        assert len(trials) == expected_total, (
            f"Total trials {len(trials)} does not match expected {expected_total} "
            f"({len(participants)} participants × {len(stimuli)} stimuli × {len(CONTEXTS)} contexts)"
        )

    def test_contexts_are_valid(self, trials):
        """Test that all relationship contexts are valid."""
        valid_contexts = set(CONTEXTS)
        
        for trial in trials:
            ctx = trial['relationship_context']
            assert ctx in valid_contexts, (
                f"Invalid context '{ctx}' found. Valid: {valid_contexts}"
            )