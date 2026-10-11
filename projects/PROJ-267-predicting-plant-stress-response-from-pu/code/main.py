"""
Entry point for the project pipeline.
"""
import argparse
import sys

# Import the shared logger. 
# We use the full path from the project root to support 'python -m code.main'
try:
    from code.utils.logging_config import get_logger
except ImportError:
    # Fallback for direct script execution 'python code/main.py'
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
    """A no‑op stage that simply logs its execution and exits 0."""
    log.info("Running NOOP stage – pipeline start")
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