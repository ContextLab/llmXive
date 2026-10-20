"""
Graceful stub for real‑data ingestion.
Writes a status JSON under ``data/logs/real_ingest_status.json`` indicating that
no verified dataset is configured.
"""

import json
import sys
from pathlib import Path
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# The required location is ``data/logs/real_ingest_status.json``.
STATUS_PATH = paths.data("logs", "real_ingest_status.json")

def main() -> int:
    message = "Data source unavailable: no verified dataset configured."
    print(message)
    log.warning(message)

    status = {
        "status": "unavailable",
        "message": message,
        "timestamp": None,
    }

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATUS_PATH.open("w") as f:
        json.dump(status, f, indent=2)

    log.info(f"Status JSON written to {STATUS_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
