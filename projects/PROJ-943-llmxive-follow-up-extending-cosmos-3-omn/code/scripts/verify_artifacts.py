"""
Task T011b: Verify model artifact and memory log existence.

This script checks for the existence of required artifacts produced by T011a:
1. code/models/proxy_hard/model.pt
2. code/logs/memory_profile.log

It exits with code 0 if all artifacts exist, or code 1 if any are missing.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_artifact(path_str: str, description: str) -> bool:
    """Check if a file exists and log the result."""
    path = Path(path_str)
    if path.exists() and path.is_file():
        logger.info(f"✓ Found {description}: {path}")
        return True
    else:
        logger.error(f"✗ Missing {description}: {path}")
        return False

def main():
    logger.info("Starting artifact verification for T011b...")

    # Define required artifacts based on T011a requirements
    artifacts = [
        ("code/models/proxy_hard/model.pt", "Model artifact (model.pt)"),
        ("code/logs/memory_profile.log", "Memory profile log (memory_profile.log)")
    ]

    all_exist = True
    for path_str, description in artifacts:
        if not check_artifact(path_str, description):
            all_exist = False

    if all_exist:
        logger.info("All required artifacts verified successfully.")
        sys.exit(0)
    else:
        logger.error("Verification failed: One or more required artifacts are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()