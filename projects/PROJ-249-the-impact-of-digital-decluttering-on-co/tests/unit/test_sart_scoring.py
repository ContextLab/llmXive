import pytest
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scoring.sart import score_sart_trial, score_sart_session

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
