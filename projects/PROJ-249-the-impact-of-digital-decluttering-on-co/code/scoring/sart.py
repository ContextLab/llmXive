from typing import List, Dict, Any, Union
import numpy as np

def score_sart_trial(trial: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score a single SART trial.
    
    Args:
        trial: Dictionary containing trial data with keys:
            - 'response_time': float (in seconds)
            - 'accuracy': bool (True if correct response, False otherwise)
            - 'stimulus_type': str ('target' or 'non-target')
    
    Returns:
        Dictionary with trial-level scoring metrics:
            - 'commission_error': bool (True if participant responded to non-target)
            - 'omission_error': bool (True if participant failed to respond to target)
            - 'response_time': float (in seconds)
    """
    stimulus_type = trial.get('stimulus_type', 'non-target')
    response_time = trial.get('response_time', 0.0)
    accuracy = trial.get('accuracy', False)
    
    # Commission error: responding when shouldn't (responding to non-target)
    commission_error = (stimulus_type == 'non-target') and (not accuracy)
    
    # Omission error: not responding when should (failing to respond to target)
    # In our schema, accuracy=False means they didn't respond correctly
    # For targets, a correct response is responding (accuracy=True)
    # For non-targets, a correct response is NOT responding (accuracy=False means they responded incorrectly)
    # Actually, let's clarify: 
    # - accuracy=True means correct behavior
    # - For targets: correct = respond -> accuracy=True means they responded
    # - For non-targets: correct = don't respond -> accuracy=True means they didn't respond
    # So omission error for target: accuracy=False (they didn't respond when they should have)
    omission_error = (stimulus_type == 'target') and (not accuracy)
    
    return {
        'commission_error': commission_error,
        'omission_error': omission_error,
        'response_time': response_time
    }

def score_sart_session(trials: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Score a complete SART session from a list of trials.
    
    Args:
        trials: List of trial dictionaries, each with keys:
            - 'response_time': float (in seconds)
            - 'accuracy': bool
            - 'stimulus_type': str ('target' or 'non-target')
    
    Returns:
        Dictionary with session-level scoring metrics:
            - 'commission_errors': int (total commission errors)
            - 'omission_errors': int (total omission errors)
            - 'mean_rt': float (mean response time for correct target responses)
    """
    if not trials:
        return {
            'commission_errors': 0,
            'omission_errors': 0,
            'mean_rt': 0.0
        }
    
    commission_errors = 0
    omission_errors = 0
    correct_target_rts = []
    
    for trial in trials:
        scored_trial = score_sart_trial(trial)
        
        if scored_trial['commission_error']:
            commission_errors += 1
        
        if scored_trial['omission_error']:
            omission_errors += 1
        
        # Collect response times for correct target responses
        # A correct target response is: stimulus_type='target' AND accuracy=True
        if trial.get('stimulus_type') == 'target' and trial.get('accuracy', False):
            rt = trial.get('response_time', 0.0)
            if rt > 0:  # Only include valid response times
                correct_target_rts.append(rt)
    
    # Calculate mean response time for correct target responses
    if correct_target_rts:
        mean_rt = float(np.mean(correct_target_rts))
    else:
        mean_rt = 0.0
    
    return {
        'commission_errors': int(commission_errors),
        'omission_errors': int(omission_errors),
        'mean_rt': mean_rt
    }
