"""
Main entry point for the project.
Initializes logging and runs the primary pipeline.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import setup_logger

def main():
    """
    Main entry point for the pipeline.
    """
    # Setup logging
    log_path = setup_logger()
    logging.info("Pipeline initialization started")
    logging.info("Log file location: %s", log_path)

    # Placeholder for future pipeline execution
    # In a real run, this would orchestrate fetcher -> graph_builder -> stats_engine
    logging.info("Pipeline ready. Use sub-modules to execute specific tasks.")
    logging.debug("Detailed debug logging is enabled.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
