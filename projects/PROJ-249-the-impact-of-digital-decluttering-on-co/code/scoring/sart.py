from typing import List, Dict, Any
import numpy as np

def score_sart_trial(trial: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a single SART trial.

    Args:
        trial: Dictionary containing:
            - response_time (float): Reaction time in seconds. 0.0 if no response.
            - accuracy (bool): True if the response was correct (target responded, non-target withheld).
            - stimulus_type (str): Either 'target' or 'non-target'.

    Returns:
        Dictionary with:
            - commission_error (bool): True if participant responded to a non-target.
            - omission_error (bool): True if participant failed to respond to a target.
            - response_time (float): The response time for this trial.
    """
    stimulus_type = trial.get('stimulus_type', '').lower()
    response_time = float(trial.get('response_time', 0.0))
    accuracy = bool(trial.get('accuracy', False))

    commission_error = False
    omission_error = False

    if stimulus_type == 'non-target':
        # Commission error: Responding to a non-target
        # If accuracy is False on a non-target, it means they responded when they shouldn't have
        if not accuracy:
            commission_error = True
    elif stimulus_type == 'target':
        # Omission error: Failing to respond to a target
        # If accuracy is False on a target, it means they didn't respond when they should have
        if not accuracy:
            omission_error = True
    else:
        # Unknown stimulus type, treat as neutral
        pass

    return {
        'commission_error': commission_error,
        'omission_error': omission_error,
        'response_time': response_time
    }

def score_sart_session(trials: List[Dict[str, Any]]) -> Dict[str, int | float | str]:
    """
    Score an entire SART session.

    Args:
        trials: List of trial dictionaries as processed by score_sart_trial.

    Returns:
        Dictionary with:
            - commission_errors (int): Total count of commission errors.
            - omission_errors (int): Total count of omission errors.
            - mean_rt (float): Mean reaction time for correct target responses
              (filtered to 100‑5000 ms).
            - low_attention (bool): True if target accuracy < 50 %.
            - quality_flag (str): One of 'valid', 'low_attention', 'missing'.
    """
    if not trials:
        return {
            'commission_errors': 0,
            'omission_errors': 0,
            'mean_rt': 0.0,
            'low_attention': False,
            'quality_flag': 'missing'
        }

    commission_count = 0
    omission_count = 0
    valid_rt_sum = 0.0
    valid_rt_count = 0
    target_correct = 0
    target_total = 0

    # RT filter bounds in seconds (100 ms – 5000 ms)
    RT_MIN = 0.1
    RT_MAX = 5.0

    # Flag to detect any out‑of‑bounds response times
    out_of_bounds = False

    for trial in trials:
        scored = score_sart_trial(trial)

        if scored['commission_error']:
            commission_count += 1
        if scored['omission_error']:
            omission_count += 1

        # Count target trials for low‑attention check
        if trial.get('stimulus_type', '').lower() == 'target':
            target_total += 1
            if trial.get('accuracy', False):
                target_correct += 1

            # Calculate mean RT only for correct target responses
            # and only if the RT falls within the accepted window
            rt = float(trial.get('response_time', 0.0))
            if rt > 0.0:
                if RT_MIN <= rt <= RT_MAX:
                    valid_rt_sum += rt
                    valid_rt_count += 1
                else:
                    out_of_bounds = True

    mean_rt = 0.0
    if valid_rt_count > 0:
        mean_rt = valid_rt_sum / valid_rt_count

    low_attention = False
    if target_total > 0:
        accuracy_rate = target_correct / target_total
        low_attention = accuracy_rate < 0.5

    # Determine quality flag
    if low_attention:
        quality_flag = 'low_attention'
    elif out_of_bounds:
        # If any response time fell outside the permitted range, we treat the session as missing
        quality_flag = 'missing'
    else:
        quality_flag = 'valid'

    return {
        'commission_errors': commission_count,
        'omission_errors': omission_count,
        'mean_rt': float(mean_rt),
        'low_attention': low_attention,
        'quality_flag': quality_flag
    }
