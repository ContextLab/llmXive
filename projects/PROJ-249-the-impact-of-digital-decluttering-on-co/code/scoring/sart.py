"""
SART (Stop-Signal Attention Response Task) scoring functions.

Implements scoring logic for commission errors, omission errors, and mean
response time based on raw trial data.
"""

from typing import List, Dict, Any, Union
import numpy as np


def score_sart_trial(trial: Dict[str, Any]) -> Dict[str, Union[int, float]]:
    """
    Score a single SART trial.

    Args:
        trial: Dictionary with keys:
            - 'response_time' (float): Time in milliseconds to respond.
            - 'accuracy' (bool): True if response was correct, False if incorrect.
            - 'stimulus_type' (str): Either 'go' or 'stop'.

    Returns:
        Dictionary with keys:
            - 'is_commission_error' (bool): True if incorrect response on 'stop' trial.
            - 'is_omission_error' (bool): True if no response on 'go' trial (RT is None or 0).
    """
    response_time = trial.get('response_time')
    accuracy = trial.get('accuracy', True)
    stimulus_type = trial.get('stimulus_type', 'go')

    is_commission_error = False
    is_omission_error = False

    # Commission error: Incorrect response on a stop signal trial
    if stimulus_type == 'stop' and not accuracy:
        is_commission_error = True

    # Omission error: No response or invalid response on a go trial
    # We consider RT <= 0 or None as a missed response
    if stimulus_type == 'go':
        if response_time is None or (isinstance(response_time, (int, float)) and response_time <= 0):
            is_omission_error = True
        elif not accuracy:
            # Some definitions count incorrect go responses as errors, but strictly:
            # Omission = missed go. Commission = false alarm on stop.
            # We track accuracy separately, but for standard SART scoring:
            # Omission is specifically failure to respond to Go.
            pass

    return {
        'is_commission_error': is_commission_error,
        'is_omission_error': is_omission_error,
        'response_time': response_time if response_time and response_time > 0 else None
    }


def score_sart_session(trials: List[Dict[str, Any]]) -> Dict[str, Union[int, float]]:
    """
    Aggregate SART scores for a session of trials.

    Args:
        trials: List of dictionaries, each matching the input schema:
            {'response_time': float, 'accuracy': bool, 'stimulus_type': str}

    Returns:
        Dictionary with:
            - 'commission_errors' (int): Total number of commission errors.
            - 'omission_errors' (int): Total number of omission errors.
            - 'mean_rt' (float): Mean response time for valid Go trials (in ms).
    """
    commission_errors = 0
    omission_errors = 0
    valid_rts = []

    for trial in trials:
        scored = score_sart_trial(trial)

        if scored['is_commission_error']:
            commission_errors += 1

        if scored['is_omission_error']:
            omission_errors += 1

        # Collect valid response times for mean calculation
        # Typically only Go trials are used for mean RT, and only if valid
        if scored['response_time'] is not None:
            # Ensure we are only counting Go trials for mean RT usually
            # But if the input doesn't specify stimulus type for RT collection logic,
            # we assume valid RTs are from Go trials where accuracy was not the primary filter for RT.
            # Standard SART: Mean RT of correct Go trials.
            if trial.get('stimulus_type') == 'go' and trial.get('accuracy', True):
                valid_rts.append(scored['response_time'])

    mean_rt = 0.0
    if valid_rts:
        mean_rt = float(np.mean(valid_rts))

    return {
        'commission_errors': commission_errors,
        'omission_errors': omission_errors,
        'mean_rt': mean_rt
    }