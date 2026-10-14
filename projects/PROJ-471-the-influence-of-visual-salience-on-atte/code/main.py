"""
Minimal entry point for the Visual Salience pipeline.

The quick‑start documentation points to ``python code/main.py --stage smoke``.
For the purpose of task T001 we provide a very small CLI that reports the
requested stage and verifies that the expected directory layout exists.
"""

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _verify_layout() -> bool:
    """Check that the core directories exist; log missing ones."""
    required = [
        paths.code(),
        paths.data("raw"),
        paths.data("interim"),
        paths.data("processed"),
        paths.data("results"),
        paths.code("tests"),
        paths.docs(),
    ]
    missing = [p for p in required if not p.is_dir()]
    if missing:
        for p in missing:
            log.error(f"Missing required directory: {p}")
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Visual Salience pipeline (smoke test)."
    )
    parser.add_argument(
        "--stage",
        choices=["smoke", "full"],
        default="smoke",
        help="Pipeline stage to execute. ``smoke`` performs a quick sanity check.",
    )
    args = parser.parse_args()

    log.info(f"Running pipeline stage: {args.stage}")

    if not _verify_layout():
        log.error("Project layout verification failed. Please run `bootstrap.py` first.")
        sys.exit(1)

    if args.stage == "smoke":
        log.info("Smoke stage completed successfully.")
    else:
        # Placeholder for the full pipeline – not implemented yet.
        log.info("Full pipeline execution is not yet implemented in this starter version.")

    sys.exit(0)


if __name__ == "__main__":
    main()
