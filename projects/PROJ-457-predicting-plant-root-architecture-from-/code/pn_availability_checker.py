import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from config import get_config, setup_logging

def log_hypothesis_unverifiable(logger: logging.Logger, state: Dict[str, Any]) -> None:
    """
    Logs the 'Hypothesis Unverifiable' status to logs/deviation.log if p_n_available is False.
    
    Args:
        logger: The configured logger instance.
        state: The current state dictionary containing 'p_n_available'.
    """
    if not state.get("p_n_available", True):
        deviation_path = get_config().get("paths", {}).get("deviation_log", "logs/deviation.log")
        logger.warning("Phosphorus/Nitrogen columns missing. Hypothesis Unverifiable.")
        
        # Ensure the log directory exists
        Path(deviation_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(deviation_path, "a", encoding="utf-8") as f:
            f.write("FR-004: Hypothesis Unverifiable - Phosphorus/Nitrogen columns missing from PlantPheno dataset. "
                    "Cannot test nutrient-architecture relationship. Proceeding with root-only data.\n")
        logger.info(f"Wrote 'Hypothesis Unverifiable' deviation to {deviation_path}")

def update_state_flag_hypothesis(state_path: Path, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates the state dictionary with the hypothesis status and writes it to disk.
    
    Args:
        state_path: Path to the state.json file.
        state: The current state dictionary.
        
    Returns:
        The updated state dictionary.
    """
    # Ensure the flag exists
    if "p_n_available" not in state:
        state["p_n_available"] = False
        
    state["hypothesis_status"] = "unverifiable" if not state.get("p_n_available", True) else "testable"
    
    # Write to disk
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        
    logging.info(f"Updated state file at {state_path} with hypothesis status: {state['hypothesis_status']}")
    return state

def main() -> None:
    """
    Main entry point for T014c: Check P/N Availability and Flag.
    Reads artifacts/state.json, checks p_n_available, logs deviation if False, and updates state.
    """
    config = get_config()
    logger = setup_logging("pn_availability_checker")
    
    state_path = Path(config.get("paths", {}).get("state_file", "artifacts/state.json"))
    
    if not state_path.exists():
        logger.error(f"State file not found at {state_path}. Prerequisite T014b failed.")
        raise FileNotFoundError(f"State file not found at {state_path}")
    
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
        
    logger.info(f"Loaded state from {state_path}: p_n_available = {state.get('p_n_available')}")
    
    # Check condition and log deviation if necessary
    log_hypothesis_unverifiable(logger, state)
    
    # Update state file with explicit status
    update_state_flag_hypothesis(state_path, state)
    
    logger.info("T014c completed successfully.")

if __name__ == "__main__":
    main()