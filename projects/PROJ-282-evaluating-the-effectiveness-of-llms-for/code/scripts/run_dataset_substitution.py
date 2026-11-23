"""
Script to execute dataset substitution logic (Task T011a).

This script is intended to be run by the orchestrator (T015) when T011 fails.
It generates the justification log and mapping rules.
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.dataset_substitution import run_dataset_substitution_logic
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run dataset substitution logic.")
    parser.add_argument(
        "--failure-reason",
        type=str,
        required=True,
        help="The reason NIST Juliet fetch failed."
    )
    args = parser.parse_args()

    log_stage_start("T011a", "Dataset Substitution Logic")
    
    try:
        logger.info(f"Executing T011a with failure reason: {args.failure_reason}")
        success = run_dataset_substitution_logic(args.failure_reason)
        
        if success:
            log_stage_complete("T011a")
            logger.info("T011a completed successfully.")
        else:
            log_stage_failure("T011a", "Logic execution failed.")
            sys.exit(1)
            
    except Exception as e:
        log_stage_failure("T011a", str(e))
        logger.error(f"Unhandled exception in T011a: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()