"""
Operation Span (Ospan) scoring module.

Implements scoring logic for the Operation Span task as defined in the project
data-model.md and task T015 requirements.

Scoring Method:
- The Ospan score is the total number of items correctly recalled in the correct
  position across all sets (span score).
- A 'trial' consists of a set of math operations and a set of words to recall.
- The input schema expects a list of trial records, where each record represents
  a single item within a set (or a set summary, depending on the data granularity).
- Based on the task description: input `data` is a list of dictionaries
  {'stimulus': str, 'recall': str, 'accuracy': bool}.
  The `accuracy` boolean indicates whether the recall matched the stimulus.

Note: This implementation assumes the input `data` is a list of dictionaries
representing individual item attempts within a session.
"""
from typing import List, Dict, Any

def score_ospan_session(
    trials: List[Dict[str, Any]]
) -> Dict[str, int | str]:
    """
    Calculate the Ospan score for a session based on a list of trial records.

    Args:
        trials: A list of dictionaries. Each dictionary must contain:
            - 'stimulus' (str): The target stimulus.
            - 'recall' (str): The recalled item.
            - 'accuracy' (bool): Whether the recall was correct.

    Returns:
        A dictionary with:
            - 'span_score' (int): The total number of correctly recalled items.
            - 'total_correct' (int): Same as span_score, representing the count of correct recalls.
            - 'quality_flag' (str): Always 'valid' for Ospan (no response‑time limits apply).

    Raises:
        ValueError: If the input data is malformed or missing required keys.
    """
    if not isinstance(trials, list):
        raise ValueError("Input 'trials' must be a list of dictionaries.")

    total_correct = 0

    for i, trial in enumerate(trials):
        if not isinstance(trial, dict):
            raise ValueError(f"Trial at index {i} is not a dictionary.")

        # Validate required keys
        required_keys = {'stimulus', 'recall', 'accuracy'}
        if not required_keys.issubset(trial.keys()):
            missing = required_keys - set(trial.keys())
            raise ValueError(f"Trial at index {i} missing keys: {missing}")

        # Validate types
        if not isinstance(trial['stimulus'], str):
            raise ValueError(f"Trial at index {i}: 'stimulus' must be a string.")
        if not isinstance(trial['recall'], str):
            raise ValueError(f"Trial at index {i}: 'recall' must be a string.")
        if not isinstance(trial['accuracy'], bool):
            raise ValueError(f"Trial at index {i}: 'accuracy' must be a boolean.")

        # Accumulate correct recalls
        if trial['accuracy']:
            total_correct += 1

    return {
        'span_score': total_correct,
        'total_correct': total_correct,
        'quality_flag': 'valid'
    }

def score_ospan_trial(
    trial: Dict[str, Any]
) -> Dict[str, int | str]:
    """
    Calculate the score for a single Ospan trial (item).

    Args:
        trial: A dictionary with 'stimulus', 'recall', and 'accuracy'.

    Returns:
        A dictionary with 'span_score' (1 if correct, 0 if incorrect),
        'total_correct' (same as span_score), and 'quality_flag' ('valid').

    Raises:
        ValueError: If the trial dictionary is malformed.
    """
    if not isinstance(trial, dict):
        raise ValueError("Input 'trial' must be a dictionary.")

    required_keys = {'stimulus', 'recall', 'accuracy'}
    if not required_keys.issubset(trial.keys()):
        missing = required_keys - set(trial.keys())
        raise ValueError(f"Trial missing keys: {missing}")

    is_correct = 1 if trial['accuracy'] else 0

    return {
        'span_score': is_correct,
        'total_correct': is_correct,
        'quality_flag': 'valid'
    }
