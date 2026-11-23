import pytest
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scoring.sart import score_sart_trial, score_sart_session
from validation.synthetic_baseline import generate_synthetic_data, write_csv
import os

class TestSartTrialScoring:
    """Unit tests for single trial SART scoring logic."""

    def test_commission_error_non_target_response(self):
        """Commission error: Responding to a non-target."""
        trial = {
            'response_time': 0.450,
            'accuracy': False,  # Did not withhold response
            'stimulus_type': 'non-target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is True
        assert result['omission_error'] is False
        assert result['response_time'] == 0.450

    def test_no_commission_non_target_withhold(self):
        """No error: Correctly withholding response to non-target."""
        trial = {
            'response_time': 0.0, # No response recorded
            'accuracy': True,     # Correct behavior (withheld)
            'stimulus_type': 'non-target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is False
        assert result['omission_error'] is False

    def test_omission_error_target_no_response(self):
        """Omission error: Failing to respond to a target."""
        trial = {
            'response_time': 0.0,
            'accuracy': False,    # Did not respond
            'stimulus_type': 'target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is False
        assert result['omission_error'] is True
        assert result['response_time'] == 0.0

    def test_correct_target_response(self):
        """No error: Correctly responding to a target."""
        trial = {
            'response_time': 0.320,
            'accuracy': True,     # Responded correctly
            'stimulus_type': 'target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is False
        assert result['omission_error'] is False
        assert result['response_time'] == 0.320

class TestSartSessionScoring:
    """Unit tests for session-level SART scoring logic."""

    def test_session_empty_trials(self):
        """Session with no trials returns zero scores."""
        trials = []
        result = score_sart_session(trials)
        assert result['commission_errors'] == 0
        assert result['omission_errors'] == 0
        assert result['mean_rt'] == 0.0

    def test_session_count_errors(self):
        """Session correctly counts commission and omission errors."""
        trials = [
            # Commission error
            {'response_time': 0.4, 'accuracy': False, 'stimulus_type': 'non-target'},
            # Omission error
            {'response_time': 0.0, 'accuracy': False, 'stimulus_type': 'target'},
            # Correct target
            {'response_time': 0.3, 'accuracy': True, 'stimulus_type': 'target'},
            # Correct non-target
            {'response_time': 0.0, 'accuracy': True, 'stimulus_type': 'non-target'},
        ]
        result = score_sart_session(trials)
        assert result['commission_errors'] == 1
        assert result['omission_errors'] == 1

    def test_session_mean_rt_calculation(self):
        """Session correctly calculates mean RT for correct target responses only."""
        trials = [
            # Commission error (should not count towards RT)
            {'response_time': 0.5, 'accuracy': False, 'stimulus_type': 'non-target'},
            # Correct target 1: 0.2s
            {'response_time': 0.2, 'accuracy': True, 'stimulus_type': 'target'},
            # Correct target 2: 0.4s
            {'response_time': 0.4, 'accuracy': True, 'stimulus_type': 'target'},
            # Omission error (should not count towards RT)
            {'response_time': 0.0, 'accuracy': False, 'stimulus_type': 'target'},
        ]
        result = score_sart_session(trials)
        # Mean of 0.2 and 0.4 is 0.3
        assert np.isclose(result['mean_rt'], 0.30, atol=0.001)

    def test_session_rt_excludes_zero(self):
        """Session excludes zero RTs from mean calculation even if marked correct."""
        trials = [
            # Correct target with 0 RT (likely an artifact or immediate response error)
            {'response_time': 0.0, 'accuracy': True, 'stimulus_type': 'target'},
            # Valid correct target
            {'response_time': 0.5, 'accuracy': True, 'stimulus_type': 'target'},
        ]
        result = score_sart_session(trials)
        # Only 0.5 should be included
        assert result['mean_rt'] == 0.5

    def test_session_output_schema(self):
        """Verify output dictionary matches required schema."""
        trials = [
            {'response_time': 0.3, 'accuracy': True, 'stimulus_type': 'target'}
        ]
        result = score_sart_session(trials)
        
        assert 'commission_errors' in result
        assert 'omission_errors' in result
        assert 'mean_rt' in result
        
        assert isinstance(result['commission_errors'], int)
        assert isinstance(result['omission_errors'], int)
        assert isinstance(result['mean_rt'], float)

class TestSartAgainstSyntheticReference:
    """
    Unit tests for SART scoring logic against the synthetic baseline data generated by T013.
    This ensures the scorer correctly processes the data format defined in the pipeline.
    """

    @pytest.fixture(scope="class")
    def synthetic_data_path(self, tmp_path_factory):
        """Generate synthetic baseline data once per test class and return path."""
        import tempfile
        import os
        
        # Create a temporary directory for this test run
        out_dir = tmp_path_factory.mktemp("synthetic_data")
        output_file = out_dir / "test_sart_reference.csv"
        
        # Generate synthetic data using the project's official generator (T013)
        # We use a fixed seed for reproducibility
        from utils.random_seed import set_global_seed
        set_global_seed(42)
        
        # Generate data for 5 participants to have enough trials
        n_participants = 5
        n_trials_per_participant = 40 
        
        data = generate_synthetic_data(
            n_participants=n_participants,
            n_trials_per_participant=n_trials_per_participant,
            seed=42
        )
        
        # Write to CSV
        write_csv(data, str(output_file))
        
        return output_file

    def test_scorer_processes_synthetic_file(self, synthetic_data_path):
        """
        Verify that score_sart_session can process a full session from the synthetic file
        without errors and returns valid metrics.
        """
        import csv
        
        # Load data
        with open(synthetic_data_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0, "Synthetic data file is empty"
        
        # Group by participant
        participants = {}
        for row in rows:
            pid = row['participant_id']
            if pid not in participants:
                participants[pid] = []
            
            # Convert types
            trial = {
                'response_time': float(row['response_time']),
                'accuracy': row['accuracy'].lower() == 'true',
                'stimulus_type': row['stimulus_type']
            }
            participants[pid].append(trial)
        
        # Test each participant's session
        for pid, trials in participants.items():
            result = score_sart_session(trials)
            
            # Assertions on output structure and types
            assert isinstance(result['commission_errors'], int), f"PID {pid}: commission_errors must be int"
            assert isinstance(result['omission_errors'], int), f"PID {pid}: omission_errors must be int"
            assert isinstance(result['mean_rt'], float), f"PID {pid}: mean_rt must be float"
            
            # Logical constraints
            assert result['commission_errors'] >= 0, f"PID {pid}: commission errors cannot be negative"
            assert result['omission_errors'] >= 0, f"PID {pid}: omission errors cannot be negative"
            
            # Mean RT constraint: if there are valid responses, RT should be > 0
            # If no valid responses, mean_rt should be 0.0
            if result['mean_rt'] > 0:
                assert result['mean_rt'] > 0.05, f"PID {pid}: mean RT seems too fast (< 50ms)"
                assert result['mean_rt'] < 2.0, f"PID {pid}: mean RT seems too slow (> 2s)"

    def test_scorer_handles_edge_case_all_commissions(self, synthetic_data_path):
        """
        Test that the scorer correctly handles a session where every non-target triggers a commission.
        We simulate this by modifying a subset of the loaded data.
        """
        import csv
        
        with open(synthetic_data_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Find a participant with non-targets
        pids = list(set([r['participant_id'] for r in rows]))
        target_pid = pids[0]
        
        trials = []
        for row in rows:
            if row['participant_id'] == target_pid:
                trial = {
                    'response_time': float(row['response_time']),
                    'accuracy': row['accuracy'].lower() == 'true',
                    'stimulus_type': row['stimulus_type']
                }
                # Force commission errors on all non-targets
                if trial['stimulus_type'] == 'non-target':
                    trial['accuracy'] = False
                    trial['response_time'] = 0.4 # Ensure non-zero RT
                trials.append(trial)
        
        result = score_sart_session(trials)
        
        # Count expected commissions
        expected_commissions = sum(1 for t in trials if t['stimulus_type'] == 'non-target' and t['accuracy'] == False)
        
        assert result['commission_errors'] == expected_commissions, \
            f"Expected {expected_commissions} commissions, got {result['commission_errors']}"

    def test_scorer_handles_edge_case_all_omissions(self, synthetic_data_path):
        """
        Test that the scorer correctly handles a session where every target is missed.
        """
        import csv
        
        with open(synthetic_data_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        pids = list(set([r['participant_id'] for r in rows]))
        target_pid = pids[0]
        
        trials = []
        for row in rows:
            if row['participant_id'] == target_pid:
                trial = {
                    'response_time': float(row['response_time']),
                    'accuracy': row['accuracy'].lower() == 'true',
                    'stimulus_type': row['stimulus_type']
                }
                # Force omissions on all targets
                if trial['stimulus_type'] == 'target':
                    trial['accuracy'] = False
                    trial['response_time'] = 0.0
                trials.append(trial)
        
        result = score_sart_session(trials)
        
        # Count expected omissions
        expected_omissions = sum(1 for t in trials if t['stimulus_type'] == 'target' and t['accuracy'] == False)
        
        assert result['omission_errors'] == expected_omissions, \
            f"Expected {expected_omissions} omissions, got {result['omission_errors']}"
        
        # Mean RT should be 0.0 if no correct target responses
        assert result['mean_rt'] == 0.0, "Mean RT should be 0.0 when all targets are omitted"