import pytest
import numpy as np
from code.scoring.sart import score_sart_trial, score_sart_session

class TestSARTScoring:
    """Unit tests for SART scoring logic against OSF reference standards."""

    def test_score_sart_trial_commission_error(self):
        """Test that commission errors are correctly identified."""
        # Non-target with incorrect response (accuracy=False) = commission error
        trial = {
            'response_time': 0.5,
            'accuracy': False,
            'stimulus_type': 'non-target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is True
        assert result['omission_error'] is False

    def test_score_sart_trial_omission_error(self):
        """Test that omission errors are correctly identified."""
        # Target with incorrect response (accuracy=False) = omission error
        trial = {
            'response_time': 0.0,  # No response time since they didn't respond
            'accuracy': False,
            'stimulus_type': 'target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is False
        assert result['omission_error'] is True

    def test_score_sart_trial_correct_target(self):
        """Test that correct target responses are identified."""
        trial = {
            'response_time': 0.45,
            'accuracy': True,
            'stimulus_type': 'target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is False
        assert result['omission_error'] is False
        assert result['response_time'] == 0.45

    def test_score_sart_trial_correct_non_target(self):
        """Test that correct non-target responses (no response) are identified."""
        trial = {
            'response_time': 0.0,
            'accuracy': True,
            'stimulus_type': 'non-target'
        }
        result = score_sart_trial(trial)
        assert result['commission_error'] is False
        assert result['omission_error'] is False

    def test_score_sart_session_commission_errors(self):
        """Test commission error counting in a session."""
        trials = [
            {'response_time': 0.5, 'accuracy': False, 'stimulus_type': 'non-target'},
            {'response_time': 0.6, 'accuracy': False, 'stimulus_type': 'non-target'},
            {'response_time': 0.4, 'accuracy': True, 'stimulus_type': 'target'},
        ]
        result = score_sart_session(trials)
        assert result['commission_errors'] == 2
        assert result['omission_errors'] == 0

    def test_score_sart_session_omission_errors(self):
        """Test omission error counting in a session."""
        trials = [
            {'response_time': 0.0, 'accuracy': False, 'stimulus_type': 'target'},
            {'response_time': 0.0, 'accuracy': False, 'stimulus_type': 'target'},
            {'response_time': 0.5, 'accuracy': True, 'stimulus_type': 'non-target'},
        ]
        result = score_sart_session(trials)
        assert result['commission_errors'] == 0
        assert result['omission_errors'] == 2

    def test_score_sart_session_mean_rt(self):
        """Test mean response time calculation for correct target responses."""
        trials = [
            {'response_time': 0.4, 'accuracy': True, 'stimulus_type': 'target'},
            {'response_time': 0.6, 'accuracy': True, 'stimulus_type': 'target'},
            {'response_time': 0.5, 'accuracy': True, 'stimulus_type': 'target'},
            # This one should not be included (non-target)
            {'response_time': 0.0, 'accuracy': True, 'stimulus_type': 'non-target'},
            # This one should not be included (incorrect target)
            {'response_time': 0.0, 'accuracy': False, 'stimulus_type': 'target'},
        ]
        result = score_sart_session(trials)
        # Mean of [0.4, 0.6, 0.5] = 0.5
        assert result['mean_rt'] == pytest.approx(0.5, rel=1e-5)

    def test_score_sart_session_empty(self):
        """Test scoring with empty trials list."""
        result = score_sart_session([])
        assert result['commission_errors'] == 0
        assert result['omission_errors'] == 0
        assert result['mean_rt'] == 0.0

    def test_score_sart_session_mixed_errors(self):
        """Test session with both commission and omission errors."""
        trials = [
            {'response_time': 0.5, 'accuracy': False, 'stimulus_type': 'non-target'},  # commission
            {'response_time': 0.0, 'accuracy': False, 'stimulus_type': 'target'},     # omission
            {'response_time': 0.4, 'accuracy': True, 'stimulus_type': 'target'},      # correct
            {'response_time': 0.0, 'accuracy': False, 'stimulus_type': 'target'},     # omission
            {'response_time': 0.6, 'accuracy': False, 'stimulus_type': 'non-target'}, # commission
        ]
        result = score_sart_session(trials)
        assert result['commission_errors'] == 2
        assert result['omission_errors'] == 2
        assert result['mean_rt'] == pytest.approx(0.4, rel=1e-5)

    def test_score_sart_session_osf_reference_pattern(self):
        """
        Test against a pattern consistent with OSF reference data (v+).
        Simulates a typical SART session with expected error rates.
        """
        # Simulate a session with ~10% commission error rate and ~5% omission error rate
        # This is typical for healthy adult participants in SART tasks
        np.random.seed(42)
        n_trials = 100
        trials = []
        
        for i in range(n_trials):
            if i % 3 == 0:  # Non-target (2/3 of trials)
                stimulus = 'non-target'
                # 10% commission error rate
                accuracy = np.random.random() > 0.10
                rt = np.random.normal(0.5, 0.1) if accuracy else 0.0
            else:  # Target (1/3 of trials)
                stimulus = 'target'
                # 5% omission error rate
                accuracy = np.random.random() > 0.05
                rt = np.random.normal(0.45, 0.08) if accuracy else 0.0
            
            trials.append({
                'response_time': max(0.0, rt),
                'accuracy': accuracy,
                'stimulus_type': stimulus
            })
        
        result = score_sart_session(trials)
        
        # Verify we got some errors (statistical expectation)
        assert result['commission_errors'] > 0
        assert result['omission_errors'] > 0
        assert result['mean_rt'] > 0.3  # Should be around 0.45s for correct targets
        assert result['mean_rt'] < 0.6  # Reasonable upper bound

    def test_score_sart_session_type_consistency(self):
        """Ensure return types match the expected schema."""
        trials = [
            {'response_time': 0.5, 'accuracy': False, 'stimulus_type': 'non-target'},
            {'response_time': 0.4, 'accuracy': True, 'stimulus_type': 'target'},
        ]
        result = score_sart_session(trials)
        
        assert isinstance(result['commission_errors'], int)
        assert isinstance(result['omission_errors'], int)
        assert isinstance(result['mean_rt'], float)
        assert 'commission_errors' in result
        assert 'omission_errors' in result
        assert 'mean_rt' in result