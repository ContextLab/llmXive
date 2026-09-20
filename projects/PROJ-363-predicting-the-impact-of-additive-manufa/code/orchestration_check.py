import os
import sys
import json
import logging
from pathlib import Path
from utils import setup_logging

def check_degenerate_status(flag_path: str) -> bool:
    """
    Check if the degenerate flag file exists.
    Returns True if degenerate (halt required), False otherwise.
    """
    logger = logging.getLogger(__name__)
    if os.path.exists(flag_path):
        logger.warning("Degenerate dataset flag detected. Halting pipeline.")
        return True
    return False

def main():
    logger = setup_logging("orchestration_check")
    
    base_dir = Path(__file__).parent.parent
    flag_path = str(base_dir / "data" / "processed" / "degenerate_flag.json")
    
    if check_degenerate_status(flag_path):
        logger.error("Pipeline halted due to degenerate dataset.")
        sys.exit(1)
    else:
        logger.info("Degenerate check passed. Proceeding.")
        sys.exit(0)

if __name__ == "__main__":
    main()