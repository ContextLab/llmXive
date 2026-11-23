import os
import sys
import logging
import yaml
import subprocess
from typing import List, Dict, Any, Optional
from utils import setup_logging, get_logger, set_task_id, get_task_id

def validate_citations(citations_path: str = "state/citations.yaml") -> bool:
    """
    T056: Validate citations from YAML file.
    """
    logger = setup_logging(task_id="T056")
    logger.info(f"Validating citations from: {citations_path}")
    
    if not os.path.exists(citations_path):
        logger.error(f"Citations file not found: {citations_path}")
        return False
    
    with open(citations_path, "r") as f:
        data = yaml.safe_load(f)
    
    # Handle nested structure
    if isinstance(data, dict) and "citations" in data:
        citations = data["citations"]
        logger.info("Detected nested 'citations' key in YAML.")
    elif isinstance(data, list):
        citations = data
    else:
        logger.error("Invalid citations structure.")
        return False
    
    valid = True
    for i, item in enumerate(citations):
        if not isinstance(item, dict):
            logger.error(f"Item {i} is not a dictionary.")
            valid = False
            continue
        
        # Check for required keys (id, title, url, source)
        required = {"id", "title", "url", "source"}
        if not required.issubset(set(item.keys())):
            logger.error(f"Item {i} missing required keys: {required - set(item.keys())}")
            valid = False
    
    if not valid:
        logger.error("Citation validation failed.")
        return False
    
    logger.info("Citation validation successful.")
    return True

def main():
    if not validate_citations():
        sys.exit(1)

if __name__ == "__main__":
    main()
