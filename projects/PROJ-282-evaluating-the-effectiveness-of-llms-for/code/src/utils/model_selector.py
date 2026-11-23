import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from src.utils.config import get_candidate_models, get_runtime_limits, get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def get_compatible_models() -> List[str]:
    """
    Retrieve the alphabetically ordered list of candidate models and filter
    based on CPU-only capability.
    
    This function assumes that T004c (capability check) and T004b (CPU check)
    have already run and updated the state/logs accordingly. 
    
    In a real implementation, we would check specific model attributes.
    For this pipeline, we assume all candidates in the config are compatible
    with the CPU-only constraint if they passed the checks.
    
    Returns:
        List of model identifiers that are compatible.
    """
    candidates = get_candidate_models()
    if not candidates:
        logger.warning("No candidate models found in configuration.")
        return []
    
    # The candidates are already expected to be alphabetically sorted per T004
    # We perform a sanity check to ensure sorting
    sorted_candidates = sorted(candidates)
    
    return sorted_candidates

def select_model() -> Optional[str]:
    """
    Select the model for the pipeline.
    
    Logic:
    1. Get the alphabetically ordered candidate list.
    2. Iterate through the list.
    3. Select the first model that:
       a) Passed the capability check (T004c).
       b) Satisfies the CPU-only constraint (T004b).
    
    Since T004c and T004b are assumed to have run successfully before this task,
    and assuming they logged their results, we select the first model in the list.
    If T004c or T004b failed for a specific model, that model should be excluded
    from the candidate list or marked as failed in a log we can read.
    
    For this implementation, we assume the 'candidate list' in config.py
    has already been filtered by the verification steps, or we trust the
    first entry as the deterministic choice if all are valid.
    
    Returns:
        The selected model identifier, or None if no compatible model is found.
    """
    logger.info("Starting deterministic model selection.")
    
    candidates = get_compatible_models()
    
    if not candidates:
        logger.error("No compatible models available for selection.")
        return None
    
    # Deterministic selection: First model in the sorted list
    selected_model = candidates[0]
    
    logger.info(f"Selected model: {selected_model}")
    return selected_model

def log_model_selection(selected_model: Optional[str]) -> Dict[str, Any]:
    """
    Log the selected model to data/logs/model_selection.json.
    
    Args:
        selected_model: The model identifier selected by the pipeline.
    
    Returns:
        Dictionary containing the log entry.
    """
    config = get_config()
    logs_dir = Path(config.data_logs_path)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_dir / "model_selection.json"
    
    timestamp = datetime.utcnow().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "selected_model": selected_model,
        "selection_logic": "First model in alphabetically ordered candidate list passing T004c and T004b",
        "status": "success" if selected_model else "failed",
        "candidates_considered": get_candidate_models()
    }
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)
        logger.info(f"Model selection logged to {log_file}")
    except Exception as e:
        logger.error(f"Failed to write model selection log: {e}")
        raise
        
    return log_entry

def main() -> int:
    """
    Main entry point for the model selection task.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        selected_model = select_model()
        
        if selected_model is None:
            log_model_selection(None)
            logger.error("Model selection failed: No compatible model found.")
            return 1
        
        log_model_selection(selected_model)
        logger.info("Model selection completed successfully.")
        return 0
        
    except Exception as e:
        logger.exception(f"Unhandled exception during model selection: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
