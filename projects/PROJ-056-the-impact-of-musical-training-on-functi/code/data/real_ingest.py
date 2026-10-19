"""
real_ingest.py
----------------
Graceful stub for real‑data ingestion.

The project currently has no verified open dataset that satisfies the
musical‑training variable requirement. According to the specification,
when no dataset is supplied the script must:

  1. Print a clear "data source unavailable" message.
  2. Write a JSON status file indicating the unavailability.
  3. Exit with status code 0 (no unhandled exception, no synthetic fallback).

This implementation follows those requirements exactly. It does **not**
attempt any download or synthetic data generation.
"""

import json
import sys
from pathlib import Path
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

STATUS_PATH = paths.data("real_ingest_status.json")

def main() -> int:
    """
    Entry point for the real‑data ingestion stub.

    Returns
    -------
    int
        Exit code 0 on successful execution (unavailability reported).
    """
    message = "Data source unavailable: no verified dataset configured."
    print(message)
    log.warning(message)

    status = {
        "status": "unavailable",
        "message": message,
        "timestamp": None,
    }

    # Ensure the parent directory exists (paths.data creates it)
    with STATUS_PATH.open("w") as f:
        json.dump(status, f, indent=2)

    log.info(f"Status JSON written to {STATUS_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
