"""
Script to initialize the logging infrastructure for the pipeline.
This script creates the necessary directory structure and configures
the root logger to write machine-readable JSON logs to logs/pipeline.log.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add the project root to the path to allow imports from code/utils
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import setup_logging, get_logger, log_event

def main():
    parser = argparse.ArgumentParser(
        description="Initialize logging infrastructure for the pipeline."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/pipeline.log",
        help="Path to the log file (default: logs/pipeline.log)"
    )
    parser.add_argument(
        "--level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Disable console output (default: False)"
    )
    args = parser.parse_args()

    log_path = Path(args.log_file)
    log_level = getattr(logging, args.level)

    # Initialize logging
    setup_logging(
        log_file=log_path,
        log_level=log_level,
        console_output=not args.no_console
    )

    logger = get_logger(__name__)
    
    # Log a startup event to verify the infrastructure is working
    log_event(
        logger,
        logging.INFO,
        "Logging infrastructure initialized successfully.",
        log_file=str(log_path),
        level=args.level
    )
    
    print(f"Logging initialized. Output written to: {log_path}")

if __name__ == "__main__":
    main()
