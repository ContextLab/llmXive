import sys
import os
from pathlib import Path
import logging
import yaml

def check_by_amendment_ratification(state_path):
    """
    Reads the constitutional state file and returns the amendment_status.
    If the file or key is missing, returns 'pending'.
    """
    state_file = Path(state_path)
    if not state_file.exists():
        logging.warning(f"State file not found: {state_file}. Assuming pending.")
        return "pending"
    
    try:
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('amendment_status', 'pending')
    except Exception as e:
        logging.error(f"Error reading state file: {e}")
        return "pending"

def enforce_gate(state_path):
    """
    Enforces the gate: exits if amendment_status is not 'ratified'.
    """
    status = check_by_amendment_ratification(state_path)
    if status != "ratified":
        logging.critical(f"Constitutional Gate Blocked: Amendment status is '{status}'. Expected 'ratified'.")
        sys.exit(1)
    logging.info("Constitutional Gate Passed.")
    return True
