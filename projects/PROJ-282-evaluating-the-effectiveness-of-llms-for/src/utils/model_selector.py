"""
Model Selector Module for llmXive Pipeline.

Implements a deterministic model selection strategy based on the candidate list
defined in config.py. Selection is based on a fixed seed and static configuration
to ensure reproducibility (Constitution I).

Constraints:
- NO runtime RAM checks for selection.
- Selected model must be compatible with all languages in the stratified sample.
- Selection is logged for auditability.
"""
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import from existing project API
from src.utils.config import get_config, CANDIDATE_MODELS
from src.utils.logger import get_logger

# Constants for deterministic selection
SEED = 42
# Mapping of languages to compatible model families (simplified for this implementation)
# In a real scenario, this would be derived from model documentation or a compatibility matrix.
# For this project, we assume the primary candidate 'Qwen2.5-Coder-7B-Instruct' supports Python, C, and JS.
SUPPORTED_LANGUAGES = {"python", "c", "javascript", "java"}
PRIMARY_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"

logger = get_logger(__name__)


def get_compatible_models(langs: List[str]) -> List[str]:
    """
    Filters the candidate model list to only those compatible with the given languages.

    Args:
        langs: List of language identifiers (e.g., ['python', 'c']).

    Returns:
        List of compatible model IDs.
    """
    if not langs:
        return []

    # Normalize languages to lowercase
    normalized_langs = {lang.lower() for lang in langs}

    compatible = []
    for model_id in CANDIDATE_MODELS:
        # For this implementation, we assume the primary model is compatible
        # with the core languages of the project.
        # In a more complex system, this would check a registry.
        if model_id == PRIMARY_MODEL_ID:
            # Check if the model supports the required languages
            # Here we assume Qwen2.5-Coder supports the defined set
            if normalized_langs.issubset(SUPPORTED_LANGUAGES):
                compatible.append(model_id)
        else:
            # Fallback logic for other candidates if defined in config
            # For now, we strictly filter based on the primary model's known capabilities
            # or a hypothetical compatibility check.
            pass

    return compatible


def select_model(langs: List[str], seed: int = SEED) -> str:
    """
    Selects a model deterministically from the candidate list.

    Logic:
    1. Filter candidates by language compatibility.
    2. If multiple compatible models exist, sort them by ID (deterministic)
       and pick the first one (or use a hash of the seed to pick one if >1).
    3. If only one, return it.
    4. If none, raise an error.

    Args:
        langs: List of languages present in the current batch.
        seed: Fixed seed for deterministic selection.

    Returns:
        The selected model ID string.

    Raises:
        ValueError: If no compatible model is found for the given languages.
    """
    logger.info(f"Starting model selection for languages: {langs}")

    compatible_models = get_compatible_models(langs)

    if not compatible_models:
        error_msg = (
            f"No compatible model found for languages: {langs}. "
            f"Available candidates: {CANDIDATE_MODELS}. "
            f"Supported languages for primary model: {SUPPORTED_LANGUAGES}."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Deterministic selection:
    # Sort the list to ensure consistent ordering regardless of insertion order
    compatible_models.sort()

    # If we have multiple, we could use a hash of the seed + language list to pick one
    # to ensure it's not always the first one if we have a pool.
    # However, for reproducibility and simplicity in this context,
    # we select the first one after sorting (which is deterministic).
    selected = compatible_models[0]

    logger.info(
        f"Model selection complete. Selected: {selected} "
        f"(Compatible with {langs}, Candidates: {CANDIDATE_MODELS})"
    )

    return selected


def get_model_config(model_id: str) -> Dict[str, Any]:
    """
    Retrieves the configuration for a specific model ID.

    Args:
        model_id: The ID of the model.

    Returns:
        Dictionary containing model configuration parameters.
    """
    # In a real implementation, this might fetch from a registry or config file.
    # Here we return a default config for the primary model.
    if model_id == PRIMARY_MODEL_ID:
        return {
            "model_id": model_id,
            "load_in_4bit": True,
            "device_map": "auto",
            "trust_remote_code": True,
            "max_length": 2048,
        }
    return {
        "model_id": model_id,
        "load_in_4bit": True,
        "device_map": "auto",
    }


def main():
    """
    Entry point for testing the model selector directly.
    """
    # Example usage
    languages = ["python", "c", "javascript"]
    try:
        model = select_model(languages)
        print(f"Selected Model: {model}")
        print(f"Config: {get_model_config(model)}")
    except ValueError as e:
        print(f"Selection Failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
