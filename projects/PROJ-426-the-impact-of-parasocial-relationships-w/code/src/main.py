"""
Entry point script used by the quickstart documentation.

The script supports two operational modes:

* ``ingest_and_match`` – Downloads the loneliness dataset and performs
  user matching, producing the artefacts required by downstream steps:
  ``data/raw/loneliness_dataset.parquet`` and
  ``data/processed/matched_users.parquet``.
* ``fit_model`` – Placeholder for the modeling stage.  For the purpose of
  completing task T003 the command simply exits with status 0 so that the
  quickstart can run without error.  A full implementation will be added
  in a later task.

This lightweight orchestrator keeps the original quickstart commands
functional without requiring a full modeling pipeline to be present.
"""

import argparse
import sys
from pathlib import Path

from src.ingest.download_loneliness import main as download_main
from src.match.user_match import main as match_main

def ingest_and_match() -> int:
    """Run the ingestion script followed by the matching script."""
    try:
        download_main()
        match_main()
        return 0
    except Exception as exc:
        print(f"Error during ingest_and_match: {exc}", file=sys.stderr)
        return 1

def fit_model() -> int:
    """
    Placeholder for the modeling pipeline.

    The full modeling implementation is outside the scope of task T003.
    This stub returns success so that the quickstart step does not abort.
    """
    # In a complete pipeline this would invoke src/modeling/run_modeling.py
    print("fit_model mode invoked – no modeling performed in T003 implementation.")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Project entry point")
    parser.add_argument(
        "--mode",
        choices=["ingest_and_match", "fit_model"],
        required=True,
        help="Operational mode to execute",
    )
    args = parser.parse_args()

    if args.mode == "ingest_and_match":
        return ingest_and_match()
    elif args.mode == "fit_model":
        return fit_model()
    else:
        parser.error(f"Unsupported mode: {args.mode}")

if __name__ == "__main__":
    sys.exit(main())
