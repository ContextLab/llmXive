import sys
import os
from pathlib import Path
import logging
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConstitutionalError(Exception):
    """Exception raised for constitutional gate violations."""
    pass

def check_by_amendment_ratification(state_path: str) -> str:
    """
    Check the status of the BY amendment in the state file.
    Returns 'ratified', 'pending', or 'missing'.
    """
    if not os.path.exists(state_path):
        logger.warning(f"State file not found: {state_path}")
        return 'missing'
    
    try:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        status = state.get('amendment_status', 'missing')
        return status
    except Exception as e:
        logger.error(f"Error reading state file: {e}")
        return 'missing'

def enforce_gate(config: dict):
    """
    Enforce the constitutional gate.
    If the amendment is not ratified, raise ConstitutionalError.
    """
    # Default state path relative to project root
    state_path = os.path.join('state', 'projects', 'PROJ-297-assessing-statistical-significance-of-ob.yaml')
    
    status = check_by_amendment_ratification(state_path)
    
    if status == 'ratified':
        logger.info("Constitutional Gate Passed: BY amendment is ratified.")
        return True
    elif status == 'pending':
        msg = "Amendment for BY procedure is pending ratification. Execution blocked."
        logger.critical(msg)
        raise ConstitutionalError(msg)
    elif status == 'missing':
        msg = "State file missing or malformed. Execution blocked."
        logger.critical(msg)
        raise ConstitutionalError(msg)
    else:
        msg = f"Unknown amendment status: {status}. Execution blocked."
        logger.critical(msg)
        raise ConstitutionalError(msg)
