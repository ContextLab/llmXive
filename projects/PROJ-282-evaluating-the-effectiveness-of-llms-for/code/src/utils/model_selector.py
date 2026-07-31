"""
Model Selector for LLM-based Security Vulnerability Detection.

Implements a deterministic model selection strategy based on the candidate list
defined in T004 (config.py). This module ensures reproducibility by avoiding
runtime RAM checks and selecting a model compatible with all target languages
(Python, C, JavaScript) as required by the stratified sample.

Constraints:
- Deterministic selection based on fixed seed/static config (No runtime RAM checks).
- Thread-safe logging.
- Compatibility with all languages in the dataset.
"""
import os
import logging
import threading
from typing import Dict, Any, Optional, List

from src.utils.config import get_config, set_seed, get_candidate_models
from src.utils.logger import get_logger

# Thread lock for safe logging in parallel contexts
_log_lock = threading.Lock()

# Supported languages for the stratified sample (from spec/plan)
SUPPORTED_LANGUAGES = {"Python", "C", "JavaScript"}

# Mapping of languages to model capabilities (simplified for selection logic)
# In a real scenario, this might be a more complex capability matrix.
# For this task, we assume the candidate models are pre-filtered for capability.
# We prioritize models known to handle multiple languages well.
MODEL_LANGUAGE_COMPATIBILITY = {
    "microsoft/Phi-3-mini-4k-instruct": {"Python", "C", "JavaScript"},
    "microsoft/Phi-3.5-mini-instruct": {"Python", "C", "JavaScript"},
    "mistralai/Mistral-7B-Instruct-v0.2": {"Python", "C", "JavaScript"},
    "google/gemma-2b-it": {"Python", "C", "JavaScript"},
    "meta-llama/Llama-2-7b-chat-hf": {"Python", "C", "JavaScript"},
    "codellama/CodeLlama-7b-Instruct-hf": {"Python", "C", "JavaScript"},
}

def _log_thread_safe(message: str, level: int = logging.INFO) -> None:
    """Thread-safe logging wrapper."""
    with _log_lock:
        logger = get_logger()
        if logger:
            logger.log(level, message)
        else:
            # Fallback to basic logging if project logger not initialized
            logging.log(level, message)

def get_compatible_models(candidate_list: Optional[List[str]] = None) -> List[str]:
    """
    Filters the candidate models to those compatible with all supported languages.

    Args:
        candidate_list: Optional list of candidate model IDs. If None, uses config.

    Returns:
        List of compatible model IDs.
    """
    if candidate_list is None:
        candidate_list = get_candidate_models()

    compatible = []
    for model_id in candidate_list:
        # Check if model is in our compatibility map
        if model_id in MODEL_LANGUAGE_COMPATIBILITY:
            capabilities = MODEL_LANGUAGE_COMPATIBILITY[model_id]
            # Check if it supports ALL required languages
            if SUPPORTED_LANGUAGES.issubset(capabilities):
                compatible.append(model_id)
        else:
            # If not in map, assume unknown but potentially compatible?
            # For strict reproducibility, we might skip unknowns or default to a safe list.
            # Here, we log a warning and skip to ensure we only pick known good models.
            _log_thread_safe(
                f"Model {model_id} not found in compatibility map. Skipping.",
                logging.WARNING
            )
            continue

    if not compatible:
        _log_thread_safe(
            "No compatible models found in the candidate list for all languages.",
            logging.ERROR
        )
        # Fallback to a known safe model if the list is empty but we must return something
        # This prevents pipeline crash, though it's a deviation.
        _log_thread_safe("Falling back to default model: microsoft/Phi-3-mini-4k-instruct", logging.WARNING)
        return ["microsoft/Phi-3-mini-4k-instruct"]

    return compatible

def select_model(seed: Optional[int] = None) -> str:
    """
    Selects a single model deterministically from the compatible list.

    Logic:
    1. Retrieve compatible models.
    2. Set seed if provided (or use global config seed).
    3. Select the first model in the sorted list to ensure determinism
       (sorting by model ID ensures order is consistent across runs).
       Alternatively, use a hash of the seed to pick an index if we want randomness
       but reproducibility. The task asks for "deterministic", which usually implies
       fixed selection or seeded selection. We will use the first model in a sorted
       list of compatible models to ensure maximum reproducibility without randomness.

    Returns:
        The selected model ID.

    Raises:
        ValueError: If no compatible models are available.
    """
    _log_thread_safe("Starting deterministic model selection...", logging.INFO)

    # 1. Get compatible models
    compatible_models = get_compatible_models()

    if not compatible_models:
        raise ValueError("No compatible models available for selection.")

    # 2. Sort for deterministic ordering (alphabetical by ID)
    compatible_models_sorted = sorted(compatible_models)

    # 3. Selection Strategy:
    #    To be strictly deterministic and reproducible without relying on a random seed
    #    for the *choice* itself (unless specified), we pick the first one in the sorted list.
    #    This satisfies "deterministic (e.g., based on a fixed seed or a static configuration)".
    #    If the requirement implies "seeded random selection", we would do:
    #    if seed is not None: set_seed(seed)
    #    idx = random.randint(0, len(compatible_models_sorted) - 1)
    #    But "static configuration" usually implies a fixed choice.
    #    We will choose the first one (index 0) of the sorted list.

    selected_model = compatible_models_sorted[0]

    _log_thread_safe(
        f"Selected model: {selected_model} (from {len(compatible_models_sorted)} compatible candidates).",
        logging.INFO
    )

    return selected_model

def select_model_with_seed(seed: int) -> str:
    """
    Selects a model using a specific seed for reproducibility.
    This version introduces a seeded random choice among compatible models
    to allow for different models to be selected in different experiments
    while remaining reproducible.
    """
    import random
    set_seed(seed)
    compatible_models = get_compatible_models()

    if not compatible_models:
        raise ValueError("No compatible models available for selection.")

    # Deterministic random selection based on seed
    selected_model = random.choice(compatible_models)

    _log_thread_safe(
        f"Selected model (seed={seed}): {selected_model}",
        logging.INFO
    )

    return selected_model

def main() -> None:
    """
    Entry point for running the model selector as a script.
    """
    _log_thread_safe("Running Model Selector standalone...", logging.INFO)
    config = get_config()
    seed = config.seed if hasattr(config, 'seed') else 42

    try:
        model = select_model_with_seed(seed)
        print(f"Selected Model: {model}")
        _log_thread_safe(f"Model selection complete: {model}", logging.INFO)
    except Exception as e:
        _log_thread_safe(f"Model selection failed: {e}", logging.ERROR)
        raise

if __name__ == "__main__":
    main()
