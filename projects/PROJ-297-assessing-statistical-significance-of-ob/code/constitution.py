import sys
import os
from pathlib import Path
import logging
import yaml

logger = logging.getLogger("constitution")

class ConstitutionalError(Exception):
    """Exception raised for constitutional gate violations."""
    pass

def check_by_amendment_ratification() -> str:
    """
    Check the status of the Benjamini-Yekutieli (BY) amendment.
    Returns: 'ratified', 'pending', or 'missing'
    """
    state_dir = Path("state/projects")
    state_file = state_dir / "PROJ-297-assessing-statistical-significance-of-ob.yaml"
    
    if not state_file.exists():
        logger.warning("Constitutional state file missing.")
        return "missing"
    
    try:
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        if not state:
            return "missing"
        
        status = state.get('amendment_status')
        if status is None:
            return "missing"
        
        return status
    except Exception as e:
        logger.error(f"Error reading constitutional state: {e}")
        return "missing"

def enforce_gate() -> None:
    """
    Enforce the constitutional gate.
    Raises ConstitutionalError if the amendment is not ratified.
    """
    status = check_by_amendment_ratification()
    
    if status == "ratified":
        logger.info("Constitutional gate passed: BY amendment ratified.")
        return
    
    if status == "pending":
        msg = "Amendment for BY procedure is pending ratification. Execution blocked."
        logger.critical(msg)
        raise ConstitutionalError(msg)
    
    if status == "missing":
        msg = "Constitutional state file missing or malformed. Execution blocked."
        logger.critical(msg)
        raise ConstitutionalError(msg)
    
    logger.warning(f"Unknown amendment status: {status}. Blocking execution.")
    raise ConstitutionalError(f"Unknown amendment status: {status}. Execution blocked.")
