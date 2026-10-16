"""
Minimal entry point for the Visual Salience project.

The quickstart guide expects the command:
    python -m code.main --stage smoke

This script provides a simple CLI that supports a ``smoke`` stage,
which runs a lightweight sanity‑check of the pipeline (currently a
no‑op that prints a success message). Additional stages can be
added later without breaking the existing interface.
"""
import argparse
import sys
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def _run_smoke_stage() -> int:
    """Perform a trivial smoke test and report success."""
    log.info("Running smoke stage – no‑op check passed.")
    print("Smoke stage completed successfully.")
    return 0

def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Visual Salience pipeline orchestrator"
    )
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        help="Pipeline stage to execute (e.g., 'smoke')",
    )
    args = parser.parse_args(argv)

    if args.stage == "smoke":
        return _run_smoke_stage()
    else:
        log.error(f"Unknown stage: {args.stage}")
        print(f"Error: unknown stage '{args.stage}'", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
