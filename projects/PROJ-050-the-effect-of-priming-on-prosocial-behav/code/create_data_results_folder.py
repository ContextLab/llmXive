"""
create_data_results_folder.py

This utility script ensures that the required ``data/results`` directory
exists. The original task T004 mistakenly created a top‑level ``results``
folder; the pipeline expects the results to be stored under ``data/results``.
Running this script is safe (idempotent) and will create the missing
directory without affecting any existing data.
"""

import sys
from llmxive_toolkit import paths, get_logger

def main() -> None:
    """
    Entry point: create the ``data/results`` directory if it does not already
    exist. The ``paths.data`` helper creates the full path and any missing
    parent directories.
    """
    log = get_logger(__name__)
    results_dir = paths.data("results")  # <project>/data/results
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        log.info("Created (or verified) data/results directory at %s", results_dir)
    except Exception as exc:
        log.error("Failed to create data/results directory: %s", exc)
        raise

if __name__ == "__main__":
    main()
