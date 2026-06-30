"""
Missing Modality Handler for Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements fallback behavior for missing modalities during benchmark execution.
- Heterogeneous condition: skips the missing modality.
- Unified condition: inserts a placeholder text representation.
"""

import logging
from typing import Any, Dict, Optional, Union, List

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants for placeholder text
MISSING_MODALITY_PLACEHOLDER = "[MISSING_MODALITY_DATA]"
MISSING_MODALITY_REASON = "Data not available or failed to load"


def handle_missing_modality(
    task_id: str,
    missing_modality: str,
    condition: str
) -> Union[str, Dict[str, Any]]:
    """
    Handle a missing modality based on the execution condition.

    Args:
        task_id: The identifier of the task being executed.
        missing_modality: The name of the missing modality (e.g., 'time_series', 'tabular', 'text').
        condition: The execution mode condition.
            - 'heterogeneous': Skips the modality (returns None/empty dict for that slot).
            - 'unified': Inserts a placeholder text string.

    Returns:
        Union[str, Dict[str, Any]]:
            - If 'unified': Returns a placeholder string describing the missing data.
            - If 'heterogeneous': Returns an empty dictionary or None to indicate skip.

    Raises:
        ValueError: If the condition is not 'heterogeneous' or 'unified'.
    """
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("task_id must be a non-empty string")
    if not isinstance(missing_modality, str) or not missing_modality:
        raise ValueError("missing_modality must be a non-empty string")
    if condition not in ('heterogeneous', 'unified'):
        raise ValueError(f"condition must be 'heterogeneous' or 'unified', got '{condition}'")

    # Log the warning as specified in requirements
    log_msg = f"WARNING: Missing modality {missing_modality} for task {task_id}"
    logger.warning(log_msg)

    if condition == 'unified':
        # Unified condition: Insert placeholder text for translation layer
        placeholder = (
            f"{MISSING_MODALITY_PLACEHOLDER} "
            f"Modality '{missing_modality}' is missing for task {task_id}. "
            f"Reason: {MISSING_MODALITY_REASON}."
        )
        logger.info(f"Unified mode: Inserted placeholder for {missing_modality}")
        return placeholder

    elif condition == 'heterogeneous':
        # Heterogeneous condition: Skip the modality
        logger.info(f"Heterogeneous mode: Skipping missing modality {missing_modality}")
        return None

def build_input_payload(
    task_id: str,
    modalities: Dict[str, Any],
    missing_modalities: List[str],
    condition: str
) -> Dict[str, Any]:
    """
    Construct the input payload for the router, handling missing modalities.

    Args:
        task_id: The task identifier.
        modalities: Dictionary of available modality data {modality_name: data}.
        missing_modalities: List of modality names expected but not present.
        condition: Execution condition ('heterogeneous' or 'unified').

    Returns:
        Dict[str, Any]: The processed modalities dictionary ready for routing.
    """
    processed_modalities = modalities.copy()

    for modality in missing_modalities:
        if modality in processed_modalities:
            continue  # Already handled or present

        # Use the handler to get the fallback value
        fallback_value = handle_missing_modality(task_id, modality, condition)

        if fallback_value is not None:
            processed_modalities[modality] = fallback_value
        else:
            # For heterogeneous, we explicitly remove or set to None to signal skip
            # depending on how the router handles None. Here we set to None.
            processed_modalities[modality] = None

    return processed_modalities
