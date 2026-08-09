"""
Scoring functions for PSS-10 and PANAS questionnaires.

This module implements the scoring logic for the Perceived Stress Scale (PSS-10)
and the Positive and Negative Affect Schedule (PANAS).

PSS-10 Scoring:
- 10 items, 5-point Likert scale (0-4)
- Items 4, 5, 7, 8 are positively worded and must be reverse-scored
- Total score is the sum of all items (0-40)
- Higher scores indicate higher perceived stress

PANAS Scoring:
- 20 items (10 Positive Affect, 10 Negative Affect)
- 5-point Likert scale (1-5) representing extent of feeling
- PA score: sum of items 1, 2, 3, 5, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20
- NA score: sum of items 4, 6, 7, 12, 18
- Note: Item numbering follows standard PANAS order
"""

from typing import List, Dict, Any, Union, Optional
import numpy as np


# PSS-10 item indices that are positively worded (0-indexed)
# Items 4, 5, 7, 8 in 1-indexed notation -> indices 3, 4, 6, 7 in 0-indexed
PSS10_POSITIVELY_WORDED_INDICES = [3, 4, 6, 7]
PSS10_MIN_VALUE = 0
PSS10_MAX_VALUE = 4

# PANAS item mappings (1-indexed to 0-indexed)
# Positive Affect items: 1, 2, 3, 5, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20
# Negative Affect items: 4, 6, 7, 12, 18
PANAS_PA_INDICES = [0, 1, 2, 4, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19]
PANAS_NA_INDICES = [3, 5, 6, 11, 17]
PANAS_MIN_VALUE = 1
PANAS_MAX_VALUE = 5


def _reverse_score_pss10(value: int) -> int:
    """
    Reverse score a PSS-10 item.
    PSS-10 uses a 0-4 scale, so reverse is: 4 - value
    """
    if not (PSS10_MIN_VALUE <= value <= PSS10_MAX_VALUE):
        raise ValueError(
            f"PSS-10 value must be between {PSS10_MIN_VALUE} and {PSS10_MAX_VALUE}, "
            f"got {value}"
        )
    return PSS10_MAX_VALUE - value


def score_pss10_session(
    responses: List[Union[int, float]],
    validate: bool = True
) -> Dict[str, Any]:
    """
    Score a PSS-10 questionnaire session.

    Args:
        responses: List of 10 integer responses (0-4 scale).
        validate: If True, validate input values and length.

    Returns:
        Dictionary with:
            - 'total_score': Sum of all items (0-40)
            - 'item_scores': List of processed item scores (after reverse scoring)
            - 'num_items': Number of items scored (should be 10)
            - 'mean_score': Average item score

    Raises:
        ValueError: If validation fails and validate=True
        TypeError: If responses is not a list or contains invalid types
    """
    if not isinstance(responses, list):
        raise TypeError("responses must be a list")

    if len(responses) != 10:
        raise ValueError(
            f"PSS-10 requires exactly 10 responses, got {len(responses)}"
        )

    item_scores = []
    for i, response in enumerate(responses):
        if not isinstance(response, (int, float)):
            raise TypeError(f"Item {i} must be numeric, got {type(response)}")

        value = int(response)

        if validate:
            if not (PSS10_MIN_VALUE <= value <= PSS10_MAX_VALUE):
                raise ValueError(
                    f"PSS-10 item {i} must be between {PSS10_MIN_VALUE} and "
                    f"{PSS10_MAX_VALUE}, got {value}"
                )

        # Reverse score positively worded items
        if i in PSS10_POSITIVELY_WORDED_INDICES:
            score = _reverse_score_pss10(value)
        else:
            score = value

        item_scores.append(score)

    total_score = sum(item_scores)

    return {
        'total_score': total_score,
        'item_scores': item_scores,
        'num_items': len(item_scores),
        'mean_score': total_score / len(item_scores) if item_scores else 0.0
    }


def score_panas_session(
    responses: List[Union[int, float]],
    validate: bool = True
) -> Dict[str, Any]:
    """
    Score a PANAS questionnaire session.

    Args:
        responses: List of 20 integer responses (1-5 scale).
        validate: If True, validate input values and length.

    Returns:
        Dictionary with:
            - 'positive_affect': Sum of positive affect items (10-50)
            - 'negative_affect': Sum of negative affect items (10-50)
            - 'pa_items': List of positive affect item scores
            - 'na_items': List of negative affect item scores
            - 'num_pa_items': Number of PA items scored (15)
            - 'num_na_items': Number of NA items scored (5)

    Raises:
        ValueError: If validation fails and validate=True
        TypeError: If responses is not a list or contains invalid types
    """
    if not isinstance(responses, list):
        raise TypeError("responses must be a list")

    if len(responses) != 20:
        raise ValueError(
            f"PANAS requires exactly 20 responses, got {len(responses)}"
        )

    pa_scores = []
    na_scores = []

    for i, response in enumerate(responses):
        if not isinstance(response, (int, float)):
            raise TypeError(f"Item {i} must be numeric, got {type(response)}")

        value = int(response)

        if validate:
            if not (PANAS_MIN_VALUE <= value <= PANAS_MAX_VALUE):
                raise ValueError(
                    f"PANAS item {i} must be between {PANAS_MIN_VALUE} and "
                    f"{PANAS_MAX_VALUE}, got {value}"
                )

        # Collect positive affect items
        if i in PANAS_PA_INDICES:
            pa_scores.append(value)

        # Collect negative affect items
        if i in PANAS_NA_INDICES:
            na_scores.append(value)

    positive_affect = sum(pa_scores)
    negative_affect = sum(na_scores)

    return {
        'positive_affect': positive_affect,
        'negative_affect': negative_affect,
        'pa_items': pa_scores,
        'na_items': na_scores,
        'num_pa_items': len(pa_scores),
        'num_na_items': len(na_scores)
    }


def score_questionnaires_batch(
    questionnaire_data: List[Dict[str, Any]],
    questionnaire_type: str
) -> List[Dict[str, Any]]:
    """
    Score a batch of questionnaire responses.

    Args:
        questionnaire_data: List of dictionaries, each containing:
            - 'participant_id': str
            - 'responses': List of numeric responses
            - Optional other metadata
        questionnaire_type: Either 'pss10' or 'panas'

    Returns:
        List of dictionaries with scoring results, each containing:
            - 'participant_id': str
            - 'scores': Dictionary of scoring results
            - 'status': 'success' or 'error'
            - 'error_message': (only if error) description of error

    Raises:
        ValueError: If questionnaire_type is not recognized
    """
    if questionnaire_type not in ['pss10', 'panas']:
        raise ValueError(
            f"questionnaire_type must be 'pss10' or 'panas', got '{questionnaire_type}'"
        )

    results = []

    for entry in questionnaire_data:
        participant_id = entry.get('participant_id', 'unknown')

        try:
            responses = entry.get('responses')
            if responses is None:
                raise ValueError("Missing 'responses' field")

            if questionnaire_type == 'pss10':
                scores = score_pss10_session(responses)
            else:  # panas
                scores = score_panas_session(responses)

            results.append({
                'participant_id': participant_id,
                'scores': scores,
                'status': 'success'
            })

        except (ValueError, TypeError, KeyError) as e:
            results.append({
                'participant_id': participant_id,
                'scores': None,
                'status': 'error',
                'error_message': str(e)
            })

    return results
