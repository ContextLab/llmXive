"""
Script to run simulation serialization and ensure output files are created.
This script is invoked by the quickstart run-book to produce
data/analysis/simulation_results.json and update data/run_log.json.
"""
import argparse
import logging
import sys
from pathlib import Path

from code.src.analysis.serialize_simulation import main as serialization_main, setup_logging

def main() -> int:
    """
    Entry point for the simulation serialization script.
    Ensures that simulation results are loaded and serialized to the
    designated output file.
    """
    parser = argparse.ArgumentParser(
        description="Run simulation serialization and produce output artifacts"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path for results (default: data/analysis/simulation_results.json)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    try:
        # Set up logging
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)

        logger.info("Starting simulation serialization process...")
        logger.info(f"Config file: {args.config}")
        logger.info(f"Output path: {args.output or 'data/analysis/simulation_results.json'}")

        # Run the serialization main function
        result = serialization_main()

        if result == 0:
            logger.info("Simulation serialization completed successfully.")
            return 0
        else:
            logger.error("Simulation serialization failed.")
            return 1

    except Exception as e:
        logging.error(f"Unexpected error during serialization: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())