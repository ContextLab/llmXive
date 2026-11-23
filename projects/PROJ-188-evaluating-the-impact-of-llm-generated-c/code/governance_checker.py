import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_constitution_amendment() -> bool:
    """
    Checks if the governance amendment for T000a has been approved.
    Returns True if the amendment is present and approved, False otherwise.
    """
    amendment_path = Path("data/governance_amendment_decision.json")
    
    if not amendment_path.exists():
        logger.error("Governance amendment file not found at: %s", amendment_path)
        return False

    try:
        with open(amendment_path, 'r', encoding='utf-8') as f:
            decision = json.load(f)
        
        if decision.get("status") != "APPROVED":
            logger.error("Governance amendment status is not APPROVED. Current status: %s", decision.get("status"))
            return False

        if decision.get("amendment_id") != "AMEND-VII-001":
            logger.warning("Unexpected amendment ID found: %s", decision.get("amendment_id"))
            # Allow proceed if status is approved, but warn
        
        logger.info("Governance amendment check PASSED. Amendment %s is approved.", decision.get("amendment_id"))
        return True

    except json.JSONDecodeError:
        logger.error("Invalid JSON in governance amendment file.")
        return False
    except Exception as e:
        logger.error("Error reading governance amendment file: %s", str(e))
        return False

def main():
    """
    Entry point for the governance checker script.
    Exits with code 0 if approved, 1 if failed.
    """
    logger.info("Starting governance check for T000a...")
    if check_constitution_amendment():
        logger.info("Governance check successful. Pipeline can proceed.")
        sys.exit(0)
    else:
        logger.error("Governance check FAILED. T000a amendment not found or not approved. Pipeline blocked.")
        sys.exit(1)

if __name__ == "__main__":
    main()