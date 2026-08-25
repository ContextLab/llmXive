"""
Finalize research by running hash_artifacts.py to update state/ and mark research complete.
This script serves as the entry point for T040.
"""
import os
import sys
import logging
from pathlib import Path

# Add the code directory to the path to allow relative imports if needed,
# though we will invoke the script via subprocess or direct function call.
# To ensure we use the local implementation, we adjust sys.path.
code_root = Path(__file__).resolve().parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.logging import init_pipeline_logging, get_logger
from utils.hash_artifacts import main as hash_main

def main():
    """
    Main entry point for finalizing research.
    1. Initialize logging.
    2. Invoke hash_artifacts.py main logic to compute hashes and update state/.
    3. Log success/failure.
    """
    # Initialize logging for the finalization step
    logger = init_pipeline_logging("finalize_research", "FINALIZE")
    logger.info("Starting research finalization process (T040).")

    try:
        # Execute the hash_artifacts logic
        # The hash_artifacts module's main() function is designed to compute
        # SHA256 hashes for data/ and code/ and update state/ JSON.
        logger.info("Invoking hash_artifacts to update state/...")
        hash_main()
        
        logger.info("Research finalization complete. State has been updated.")
        return 0
    except Exception as e:
        logger.error(f"Research finalization failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())