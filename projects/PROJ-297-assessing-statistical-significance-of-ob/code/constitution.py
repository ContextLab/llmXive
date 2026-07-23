import sys
import os
from pathlib import Path
import logging
import yaml

class ConstitutionalError(Exception):
    """Exception raised when constitutional gate checks fail."""
    pass

def check_by_amendment_ratification(state_path: str) -> bool:
    """
    Check the ratification status of the BY procedure amendment.
    Returns True if ratified, False otherwise.
    """
    if not os.path.exists(state_path):
        return False
    
    try:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
            status = state.get('amendment_status', 'pending')
            return status == 'ratified'
    except Exception:
        return False

def enforce_gate(logger: logging.Logger):
    """
    Enforce the constitutional gate.
    Halts execution if the amendment is not ratified.
    """
    state_path = "state/projects/PROJ-297-assessing-statistical-significance-of-ob.yaml"
    
    # Ensure state directory exists
    os.makedirs("state/projects", exist_ok=True)
    
    # If file doesn't exist, create it with pending status (bridge for local dev)
    if not os.path.exists(state_path):
        logger.warning(f"State file {state_path} not found. Creating with pending status.")
        with open(state_path, 'w') as f:
            yaml.dump({'amendment_status': 'pending', 'ratified_by': None, 'date': None}, f)
    
    if not check_by_amendment_ratification(state_path):
        msg = "Amendment for BY procedure is pending ratification. Execution blocked."
        logger.error(msg)
        raise ConstitutionalError(msg)
    
    logger.info("Constitutional gate passed: BY procedure amendment is ratified.")
