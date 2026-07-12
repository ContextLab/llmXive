"""
Questionnaire scoring functions for PSS-10 and PANAS.

This module implements scoring logic for:
- Perceived Stress Scale (PSS-10)
- Positive and Negative Affect Schedule (PANAS)
"""

from typing import List, Dict, Any, Union, Optional
import numpy as np


# PSS-10 Reverse Scoring Map
# PSS-10 items 1, 2, 4, 5, 6, 7, 9, 10 are positive (direct scoring)
# PSS-10 items 3, 8 are negative (reverse scoring: 0->4, 1->3, 2->2, 3->1, 4->0)
# Note: Responses are typically 0-4 (Never, Almost Never, Sometimes, Fairly Often, Very Often)
PSS10_REVERSE_ITEMS = {2, 7}  # 0-indexed: items 3 and 8 in 1-indexed notation

# PANAS Scales
# Positive Affect items: 1, 3, 5, 9, 10, 12, 14, 16, 17, 18
# Negative Affect items: 2, 4, 6, 7, 8, 11, 13, 15
# 0-indexed:
PANAS_POSITIVE_ITEMS = {0, 2, 4, 8, 9, 11, 13, 15, 16, 17}
PANAS_NEGATIVE_ITEMS = {1, 3, 5, 6, 7, 10, 12, 14}


def score_pss10_session(
    responses: Union[List[int], Dict[str, int]]
) -> Dict[str, Any]:
    """
    Score a PSS-10 (Perceived Stress Scale) session.

    Args:
        responses: A list of 10 integer responses (0-4) or a dict mapping
                   item names to values. If a list, items are assumed to be
                   ordered 1 through 10.

    Returns:
        A dictionary with:
            - 'total_score': Sum of all item scores (0-40)
            - 'item_scores': List of individual item scores (after reverse scoring)
            - 'num_items': Number of items scored (should be 10)
            - 'mean_score': Mean item score

    Raises:
        ValueError: If responses are not 0-4 or count is not 10.
    """
    # Normalize input to list
    if isinstance(responses, dict):
        # Expect keys like 'item_1' to 'item_10' or '1' to '10'
        if len(responses) != 10:
            raise ValueError(f"PSS-10 requires exactly 10 items, got {len(responses)}")
        
        # Extract values in order
        # Try to sort by integer key if possible
        try:
            sorted_items = sorted(responses.items(), key=lambda x: int(x[0].replace('item_', '')))
            values = [v for _, v in sorted_items]
        except (ValueError, KeyError):
            # Fallback: assume order of dict (Python 3.7+) or sort by key string
            values = [responses[k] for k in sorted(responses.keys())]
    else:
        values = list(responses)

    if len(values) != 10:
        raise ValueError(f"PSS-10 requires exactly 10 items, got {len(values)}")

    # Validate range
    for i, v in enumerate(values):
        if not isinstance(v, (int, float)) or v < 0 or v > 4:
            raise ValueError(f"Item {i+1} value {v} is not in valid range [0, 4]")

    # Apply reverse scoring for items 3 and 8 (indices 2 and 7)
    scored_items = []
    for i, v in enumerate(values):
        if i in PSS10_REVERSE_ITEMS:
            # Reverse: 0->4, 1->3, 2->2, 3->1, 4->0
            scored = 4 - int(v)
        else:
            scored = int(v)
        scored_items.append(scored)

    total = sum(scored_items)
    mean_val = total / len(scored_items)

    return {
        'total_score': total,
        'item_scores': scored_items,
        'num_items': len(scored_items),
        'mean_score': mean_val,
        'scale': 'PSS-10'
    }


def score_panas_session(
    responses: Union[List[int], Dict[str, int]],
    scale_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Score a PANAS (Positive and Negative Affect Schedule) session.

    PANAS consists of 20 items: 10 Positive Affect (PA) and 10 Negative Affect (NA).
    Responses are typically on a 1-5 scale (1 = Very slightly or not at all, 5 = Extremely).

    Args:
        responses: A list of 20 integer responses (1-5) or a dict mapping
                   item names to values. If a list, items are assumed to be
                   ordered 1 through 20.
        scale_type: Optional. If 'positive', only return PA score. If 'negative',
                    only return NA score. If None, return both.

    Returns:
        A dictionary with:
            - 'positive_affect': Sum of PA items (10-50)
            - 'negative_affect': Sum of NA items (10-50)
            - 'total_affect': Sum of both (20-100) - only if scale_type is None
            - 'item_scores': List of all 20 item scores
            - 'num_items': Number of items scored (should be 20)
            - 'positive_mean': Mean of PA items
            - 'negative_mean': Mean of NA items

    Raises:
        ValueError: If responses are not 1-5 or count is not 20.
    """
    # Normalize input to list
    if isinstance(responses, dict):
        if len(responses) != 20:
            raise ValueError(f"PANAS requires exactly 20 items, got {len(responses)}")
        
        # Extract values in order
        try:
            sorted_items = sorted(responses.items(), key=lambda x: int(x[0].replace('item_', '')))
            values = [v for _, v in sorted_items]
        except (ValueError, KeyError):
            values = [responses[k] for k in sorted(responses.keys())]
    else:
        values = list(responses)

    if len(values) != 20:
        raise ValueError(f"PANAS requires exactly 20 items, got {len(values)}")

    # Validate range
    for i, v in enumerate(values):
        if not isinstance(v, (int, float)) or v < 1 or v > 5:
            raise ValueError(f"Item {i+1} value {v} is not in valid range [1, 5]")

    int_values = [int(v) for v in values]

    # Calculate Positive Affect
    pa_items = [int_values[i] for i in PANAS_POSITIVE_ITEMS]
    pa_score = sum(pa_items)
    pa_mean = pa_score / len(pa_items)

    # Calculate Negative Affect
    na_items = [int_values[i] for i in PANAS_NEGATIVE_ITEMS]
    na_score = sum(na_items)
    na_mean = na_score / len(na_items)

    result: Dict[str, Any] = {
        'positive_affect': pa_score,
        'negative_affect': na_score,
        'item_scores': int_values,
        'num_items': len(int_values),
        'positive_mean': pa_mean,
        'negative_mean': na_mean,
        'scale': 'PANAS'
    }

    if scale_type is None:
        result['total_affect'] = pa_score + na_score
        result['total_mean'] = result['total_affect'] / len(int_values)

    return result


def score_questionnaires_batch(
    batch_data: List[Dict[str, Any]],
    pss10_key: str = 'pss10_responses',
    panas_key: str = 'panas_responses'
) -> List[Dict[str, Any]]:
    """
    Score a batch of questionnaire responses.

    Args:
        batch_data: List of dictionaries, each containing participant data.
                    Expected keys: 'participant_id', 'pss10_responses', 'panas_responses'
        pss10_key: Key name for PSS-10 responses in input dict
        panas_key: Key name for PANAS responses in input dict

    Returns:
        List of dictionaries with scoring results for each participant.
    """
    results = []
    for entry in batch_data:
        participant_id = entry.get('participant_id', 'unknown')
        result_entry = {'participant_id': participant_id}

        # Score PSS-10
        if pss10_key in entry:
            try:
                pss_result = score_pss10_session(entry[pss10_key])
                result_entry.update({
                    f'pss10_{k}': v for k, v in pss_result.items()
                })
            except ValueError as e:
                result_entry['pss10_error'] = str(e)

        # Score PANAS
        if panas_key in entry:
            try:
                panas_result = score_panas_session(entry[panas_key])
                result_entry.update({
                    f'panas_{k}': v for k, v in panas_result.items()
                })
            except ValueError as e:
                result_entry['panas_error'] = str(e)

        results.append(result_entry)

    return results