import os
import logging
import threading
from typing import Dict, Any, Optional, List

from src.utils.config import get_config, set_seed, get_candidate_models
from src.utils.logger import get_logger

# Thread-safe logger lock for parallel execution contexts
_log_lock = threading.Lock()

# Capability map: Model -> Supported Languages
# These are deterministic, static configurations.
# Based on typical capabilities of CPU-compatible quantized models.
MODEL_CAPABILITIES = {
    "microsoft/phi-2": ["Python", "JavaScript", "C", "C++", "Java", "Go"],
    "microsoft/phi-1.5": ["Python", "JavaScript", "C", "C++", "Java"],
    "stabilityai/stable-code-3b": ["Python", "JavaScript", "C", "C++"],
    "bigcode/starcoderbase-1b": ["Python", "JavaScript", "C", "C++", "Java", "Go", "Rust"],
    "Salesforce/codegen-6B-mono": ["Python", "JavaScript", "C", "C++", "Java"],
    "codellama/CodeLlama-7b-hf": ["Python", "JavaScript", "C", "C++", "Java", "Go", "Rust"],
}

# Required languages for the stratified sample (from T012/US1)
REQUIRED_LANGUAGES = {"Python", "JavaScript", "C"}

def get_compatible_models(candidate_models: Optional[List[str]] = None) -> List[str]:
    """
    Filter the candidate list to only models that support all required languages
    (C, Python, JavaScript) based on the static capability map.
    
    Args:
        candidate_models: Optional override list. If None, uses config list.
        
    Returns:
        List of model IDs that are compatible with the required languages.
    """
    if candidate_models is None:
        candidate_models = get_candidate_models()
    
    compatible = []
    logger = get_logger("model_selector")
    
    for model_id in candidate_models:
        if model_id not in MODEL_CAPABILITIES:
            logger.warning(f"Model '{model_id}' not found in capability map. Skipping.")
            continue
        
        supported = set(MODEL_CAPABILITIES[model_id])
        if REQUIRED_LANGUAGES.issubset(supported):
            compatible.append(model_id)
        else:
            missing = REQUIRED_LANGUAGES - supported
            logger.info(f"Model '{model_id}' missing support for: {missing}. Skipping.")
    
    return compatible

def select_model_with_seed(seed: int = 42, candidate_models: Optional[List[str]] = None) -> str:
    """
    Deterministically select a model from the compatible list using a fixed seed.
    This ensures reproducibility across runs (Constitution Principle I).
    
    Args:
        seed: The random seed for selection.
        candidate_models: Optional override list.
        
    Returns:
        The selected model ID.
        
    Raises:
        ValueError: If no compatible models are found.
    """
    # Set seed for deterministic selection
    set_seed(seed)
    
    compatible = get_compatible_models(candidate_models)
    
    logger = get_logger("model_selector")
    
    if not compatible:
        error_msg = "No candidate models support all required languages (C, Python, JavaScript)."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Deterministic selection: sort to ensure order, then pick based on seed
    # Using sorted() ensures the list is ordered consistently regardless of dict/set iteration
    sorted_compatible = sorted(compatible)
    
    # Use a simple deterministic index based on seed
    # If we have N models, index = seed % N
    import random
    rng = random.Random(seed)
    selected_index = rng.randint(0, len(sorted_compatible) - 1)
    selected_model = sorted_compatible[selected_index]
    
    with _log_lock:
        logger.info(f"Deterministic selection (seed={seed}): Selected '{selected_model}' from {len(sorted_compatible)} candidates.")
        logger.info(f"Capabilities: {MODEL_CAPABILITIES.get(selected_model, 'Unknown')}")
    
    return selected_model

def select_model() -> str:
    """
    Main entry point for model selection. Uses the default seed from config.
    """
    config = get_config()
    seed = config.runtime_config.seed if hasattr(config, 'runtime_config') else 42
    return select_model_with_seed(seed=seed)

def main():
    """
    CLI entry point to demonstrate model selection.
    """
    logger = get_logger("model_selector")
    logger.info("Starting model selection process...")
    
    try:
        selected = select_model()
        logger.info(f"Selection complete. Model: {selected}")
        return selected
    except Exception as e:
        logger.error(f"Model selection failed: {e}")
        raise

if __name__ == "__main__":
    main()
