"""
Runner script for T028b: Derive Dilemma Choice.
Orchestrates the execution of derive_dilemma_choice.py with appropriate logging.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the path if not already present
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger
from derive_dilemma_choice import main as derive_main

def main():
    # Setup logging
    logger = setup_logging("derive_dilemma_choice")
    data_logger = get_data_quality_logger()

    logger.info("Starting T028b: Derive Dilemma Choice")

    try:
        # Execute the main logic
        # Note: The actual arguments are expected to be passed via command line
        # when this script is invoked by the pipeline runner.
        # However, for direct execution, we assume standard defaults or CLI args.
        # The 'derive_dilemma_choice' module handles its own argparse.
        # We simply invoke its main.
        derive_main()
        logger.info("T028b: Derive Dilemma Choice completed successfully.")
    except Exception as e:
        logger.error(f"T028b: Derive Dilemma Choice failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
