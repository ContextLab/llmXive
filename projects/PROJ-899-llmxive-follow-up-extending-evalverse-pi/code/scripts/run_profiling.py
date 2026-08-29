import os
import sys
import logging
from pathlib import Path

from src.data.profiles import main as profiling_main
from src.utils import setup_logging

def main():
    """Wrapper script to run the profiling task with default paths."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Default paths relative to project root
    project_root = Path(__file__).parent.parent
    scores_path = project_root / "data" / "processed" / "scores.csv"
    output_path = project_root / "data" / "profiling_logs.json"

    if not scores_path.exists():
        logger.error(f"Input file not found: {scores_path}")
        logger.error("Please ensure T042 has completed and data/processed/scores.csv exists.")
        sys.exit(1)

    logger.info(f"Running profiling on {scores_path}")
    logger.info(f"Output will be saved to {output_path}")

    # Set up arguments for the profiling main function
    sys.argv = [
        "run_profiling.py",
        "--input", str(scores_path),
        "--output", str(output_path),
        "--seed", "42"
    ]

    profiling_main()
    logger.info("Profiling task completed successfully.")

if __name__ == "__main__":
    main()