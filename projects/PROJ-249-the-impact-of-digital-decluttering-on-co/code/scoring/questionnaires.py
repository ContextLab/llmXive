"""
Scoring functions for PSS-10 and PANAS questionnaires.

Implements scoring logic for:
- PSS-10: Perceived Stress Scale (10 items)
- PANAS: Positive and Negative Affect Schedule (20 items)

Adheres to data-model.md schema and FR-009 validation requirements.
"""

from typing import List, Dict, Any, Union, Optional
import numpy as np


def score_pss10_session(
    responses: Dict[str, Union[int, float, str]],
    reverse_items: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Score a PSS-10 session from raw responses.

    The PSS-10 consists of 10 items rated 0-4 (Never, Almost Never, Sometimes,
    Fairly Often, Very Often). Items 4, 5, 7, and 8 are reverse-scored.

    Args:
        responses: Dictionary mapping item keys (e.g., 'pss_1' to 'pss_10') to
                   raw integer responses (0-4).
        reverse_items: List of keys to reverse-score. Defaults to standard PSS-10
                       reverse items: ['pss_4', 'pss_5', 'pss_7', 'pss_8'].

    Returns:
        Dictionary with:
            - 'total_score': Sum of all item scores (0-40)
            - 'mean_score': Mean of all item scores (0-4)
            - 'n_items': Number of valid items scored
            - 'valid': Boolean indicating if all 10 items were present

    Raises:
        ValueError: If response values are outside valid range (0-4)
        KeyError: If required item keys are missing
    """
    if reverse_items is None:
        reverse_items = ['pss_4', 'pss_5', 'pss_7', 'pss_8']

    expected_items = [f'pss_{i}' for i in range(1, 11)]
    missing_items = [item for item in expected_items if item not in responses]

    if missing_items:
        raise KeyError(f"Missing required PSS-10 items: {missing_items}")

    total = 0.0
    valid_count = 0

    for item_key in expected_items:
        raw_value = responses[item_key]

        # Validate range
        if not isinstance(raw_value, (int, float)):
            raise ValueError(f"Invalid response type for {item_key}: {type(raw_value)}")
        if raw_value < 0 or raw_value > 4:
            raise ValueError(f"Invalid PSS-10 response for {item_key}: {raw_value}. Must be 0-4.")

        score = float(raw_value)

        # Reverse score if needed
        if item_key in reverse_items:
            score = 4.0 - score

        total += score
        valid_count += 1

    mean_score = total / valid_count if valid_count > 0 else 0.0
    is_valid = valid_count == 10

    return {
        'total_score': total,
        'mean_score': mean_score,
        'n_items': valid_count,
        'valid': is_valid
    }


def score_panas_session(
    responses: Dict[str, Union[int, float, str]],
    time_frame: str = 'past_week'
) -> Dict[str, float]:
    """
    Score a PANAS session from raw responses.

    PANAS consists of 20 items (10 positive affect, 10 negative affect)
    rated 1-5 (Very slightly or not at all to Extremely).

    Positive items: 1, 2, 3, 5, 9, 10, 12, 13, 14, 17
    Negative items: 4, 6, 7, 8, 11, 15, 16, 18, 19, 20

    Args:
        responses: Dictionary mapping item keys (e.g., 'panas_1' to 'panas_20')
                   to raw integer responses (1-5).
        time_frame: Time frame context for the score (e.g., 'past_week', 'today').
                   Used for metadata, does not affect calculation.

    Returns:
        Dictionary with:
            - 'positive_affect': Sum of positive items (10-50)
            - 'negative_affect': Sum of negative items (10-50)
            - 'total_affect': Sum of both (20-100)
            - 'mean_positive': Mean of positive items (1-5)
            - 'mean_negative': Mean of negative items (1-5)
            - 'n_positive': Number of valid positive items
            - 'n_negative': Number of valid negative items
            - 'valid': Boolean indicating if all 20 items were present

    Raises:
        ValueError: If response values are outside valid range (1-5)
        KeyError: If required item keys are missing
    """
    positive_items = [f'panas_{i}' for i in [1, 2, 3, 5, 9, 10, 12, 13, 14, 17]]
    negative_items = [f'panas_{i}' for i in [4, 6, 7, 8, 11, 15, 16, 18, 19, 20]]
    all_items = positive_items + negative_items

    missing_items = [item for item in all_items if item not in responses]
    if missing_items:
        raise KeyError(f"Missing required PANAS items: {missing_items}")

    pos_total = 0.0
    neg_total = 0.0
    valid_pos = 0
    valid_neg = 0

    for item_key in positive_items:
        raw_value = responses[item_key]
        if not isinstance(raw_value, (int, float)):
            raise ValueError(f"Invalid response type for {item_key}: {type(raw_value)}")
        if raw_value < 1 or raw_value > 5:
            raise ValueError(f"Invalid PANAS response for {item_key}: {raw_value}. Must be 1-5.")

        pos_total += float(raw_value)
        valid_pos += 1

    for item_key in negative_items:
        raw_value = responses[item_key]
        if not isinstance(raw_value, (int, float)):
            raise ValueError(f"Invalid response type for {item_key}: {type(raw_value)}")
        if raw_value < 1 or raw_value > 5:
            raise ValueError(f"Invalid PANAS response for {item_key}: {raw_value}. Must be 1-5.")

        neg_total += float(raw_value)
        valid_neg += 1

    mean_pos = pos_total / valid_pos if valid_pos > 0 else 0.0
    mean_neg = neg_total / valid_neg if valid_neg > 0 else 0.0
    is_valid = valid_pos == 10 and valid_neg == 10

    return {
        'positive_affect': pos_total,
        'negative_affect': neg_total,
        'total_affect': pos_total + neg_total,
        'mean_positive': mean_pos,
        'mean_negative': mean_neg,
        'n_positive': valid_pos,
        'n_negative': valid_neg,
        'valid': is_valid,
        'time_frame': time_frame
    }


def score_questionnaires_batch(
    batch_responses: List[Dict[str, Any]],
    questionnaire_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Score multiple questionnaire sessions in a batch.

    Args:
        batch_responses: List of dictionaries, each containing responses for
                         either PSS-10, PANAS, or both.
        questionnaire_types: List of questionnaire types to score ('pss10', 'panas').
                             Defaults to both if not specified.

    Returns:
        List of scoring results, one per input record, containing original data
        plus computed scores.
    """
    if questionnaire_types is None:
        questionnaire_types = ['pss10', 'panas']

    results = []

    for idx, record in enumerate(batch_responses):
        result = {'record_index': idx, 'original_data': record.copy()}

        # Extract participant ID if present
        if 'participant_id' in record:
            result['participant_id'] = record['participant_id']

        # Score PSS-10 if present and requested
        if 'pss10' in questionnaire_types:
            # Look for PSS items in the record
            pss_items = {k: v for k, v in record.items() if k.startswith('pss_')}
            if pss_items:
                try:
                    result['pss10_scores'] = score_pss10_session(pss_items)
                except (KeyError, ValueError) as e:
                    result['pss10_scores'] = None
                    result['pss10_error'] = str(e)
            else:
                result['pss10_scores'] = None

        # Score PANAS if present and requested
        if 'panas' in questionnaire_types:
            panas_items = {k: v for k, v in record.items() if k.startswith('panas_')}
            if panas_items:
                try:
                    result['panas_scores'] = score_panas_session(panas_items)
                except (KeyError, ValueError) as e:
                    result['panas_scores'] = None
                    result['panas_error'] = str(e)
            else:
                result['panas_scores'] = None

        results.append(result)

    return results

# Export public API
__all__ = [
    'score_pss10_session',
    'score_panas_session',
    'score_questionnaires_batch'
]
