"""Execute Corruption Injection for all generated workflows.

This script invokes the `CorruptionInjector` implementation to apply
corruption to the execution logs of every workflow generated in the
current sweep. It writes the corrupted logs to
`data/processed/corrupted_logs/` and updates the central
`data/processed/corruption_map.json` artifact.

The script is intended to be run directly (e.g. `python code/exec_corruption.py`)
or invoked from the pipeline's `main.py` with the appropriate phase.
"""

import logging
import os
import sys

# Local project imports
from config import ensure_directories
from simulators.corruption_injector import main as corruption_main

# Configure a simple logger for this script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

def run():
    """Run the corruption injection process."""
    logger.info("Ensuring project directories exist.")
    ensure_directories()

    logger.info("Starting corruption injection for all workflows.")
    # The `corruption_main` function encapsulates the iteration over
    # workflow IDs, application of the configured corruption rate,
    # writing of corrupted logs, and updating of the central map.
    # It raises any exception it encounters, which will cause the
    # script to exit with a non‑zero status – this is intentional so
    # the execution stage can detect failures.
    corruption_main()
    logger.info("Corruption injection completed successfully.")

if __name__ == "__main__":
    run()
