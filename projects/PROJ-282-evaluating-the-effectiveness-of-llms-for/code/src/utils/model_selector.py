"""
Model Selection Module for llmXive Pipeline.

This module implements the deterministic model selection logic (T004a).
It selects the first model from the candidate list that passes capability checks
and logs the selection to data/logs/model_selection.json.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from src.utils.config import get_config, set_seed, get_candidate_models
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

# Constants
MODEL_SELECTION_LOG_PATH = "data/logs/model_selection.json"


def get_compatible_models(capability_check_results: Optional[Dict[str, bool]] = None) -> List[str]:
    """
    Filter candidate models based on capability check results.

    Args:
        capability_check_results: Dict mapping model names to boolean capability status.
            If None, assumes all candidates are compatible (fallback).

    Returns:
        List of model names that are compatible.
    """
    candidate_models = get_candidate_models()
    if not candidate_models:
        logging.warning("No candidate models found in configuration.")
        return []

    if capability_check_results is None:
        # Fallback: if no results provided, return all candidates
        logging.warning("No capability check results provided. Returning all candidate models.")
        return candidate_models

    compatible = []
    for model_name in candidate_models:
        # Check if model passed capability check
        if capability_check_results.get(model_name, False):
            compatible.append(model_name)
        else:
            logging.info(f"Model '{model_name}' failed capability check or not in results.")

    return compatible


def select_model_with_seed(capability_check_results: Optional[Dict[str, bool]] = None) -> str:
    """
    Deterministically select the first compatible model from the candidate list.

    This implements the T004a requirement: select the first model in the candidate list
    (from T004) that passes the capability check in T004c.

    Args:
        capability_check_results: Dict mapping model names to boolean capability status.

    Returns:
        The name of the selected model.

    Raises:
        ValueError: If no compatible models are found.
    """
    set_seed(42)  # Ensure deterministic behavior
    compatible_models = get_compatible_models(capability_check_results)

    if not compatible_models:
        raise ValueError(
            "No compatible models found. "
            "Ensure T004c (Model Capability Verification) has been executed successfully "
            "and capability_check_results contain at least one passing model."
        )

    # Deterministic selection: first in the list
    selected_model = compatible_models[0]
    logging.info(f"Deterministically selected model: {selected_model}")
    return selected_model


def select_model(capability_check_results: Optional[Dict[str, bool]] = None) -> str:
    """
    Main entry point for model selection.

    Selects the model and logs the result to data/logs/model_selection.json.

    Args:
        capability_check_results: Dict mapping model names to boolean capability status.

    Returns:
        The name of the selected model.
    """
    logger = get_logger(__name__)
    log_stage_start(logger, "Model Selection (T004a)")

    try:
        selected_model = select_model_with_seed(capability_check_results)

        # Prepare selection record
        selection_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "selected_model": selected_model,
            "candidate_models": get_candidate_models(),
            "compatible_models": get_compatible_models(capability_check_results),
            "capability_check_results": capability_check_results or {},
            "selection_logic": "First compatible model from candidate list (deterministic)",
            "status": "success"
        }

        # Ensure log directory exists
        log_dir = Path(MODEL_SELECTION_LOG_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Write selection log
        with open(MODEL_SELECTION_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(selection_record, f, indent=2)

        log_stage_complete(
            logger,
            "Model Selection (T004a)",
            artifact_path=MODEL_SELECTION_LOG_PATH
        )

        return selected_model

    except Exception as e:
        log_stage_failure(
            logger,
            "Model Selection (T004a)",
            error=str(e)
        )
        raise


def main() -> str:
    """
    CLI entry point for model selection.

    Reads capability check results from data/logs/model_capability_check.json
    (if it exists) and performs model selection.

    Returns:
        The name of the selected model.
    """
    logger = get_logger(__name__)
    capability_check_path = Path("data/logs/model_capability_check.json")

    capability_check_results = None
    if capability_check_path.exists():
        try:
            with open(capability_check_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Expecting a dict with model names as keys and boolean status
                capability_check_results = data.get("capability_results", {})
                logger.info(f"Loaded capability check results from {capability_check_path}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse capability check results: {e}. Proceeding without results.")
    else:
        logger.warning(f"Capability check file not found at {capability_check_path}. Proceeding without results.")

    selected_model = select_model(capability_check_results)
    logger.info(f"Model selection complete. Selected: {selected_model}")
    return selected_model


if __name__ == "__main__":
    main()
