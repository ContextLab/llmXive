"""
Entry point for the project pipeline.

The original ``main.py`` (created in T001) supported a ``--stage noop``
command that exited with status 0.  This implementation now imports the
project‑wide logger defined in ``utils.logging_config`` so that *any*
invocation of the script creates ``logs/pipeline.log`` and records a
basic start‑up message.  Additional stages can be added later; for the
purpose of T006 the ``noop`` stage is sufficient to demonstrate that the
logger is used throughout the code base.
"""

import argparse
import sys

# Import the shared logger.  Using the wrapper in ``utils.logging_config``
# ensures compatibility with existing imports throughout the project.
from utils.logging_config import get_logger

log = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Project pipeline entry point"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="noop",
        help="Pipeline stage to execute (default: noop)",
    )
    return parser.parse_args()

def run_noop():
    """A no‑op stage that simply logs its execution."""
    log.info("Running NOOP stage – pipeline start")
    # No further processing; this satisfies the verification that a
    # pipeline run creates the log file.
    log.info("NOOP stage completed successfully")
    return 0

def main():
    args = parse_args()
    if args.stage == "noop":
        exit_code = run_noop()
    else:
        log.error(f"Unknown stage requested: {args.stage}")
        exit_code = 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()