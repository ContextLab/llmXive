"""
Graceful stub for real‑data ingestion.
"""
import json
import sys
from pathlib import Path
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)
STATUS_PATH = paths.data("real_ingest_status.json")

def main() -> int:
    message = "Data source unavailable: no verified dataset configured."
    print(message)
    log.warning(message)

    status = {
        "status": "unavailable",
        "message": message,
        "timestamp": None,
    }

    with STATUS_PATH.open("w") as f:
        json.dump(status, f, indent=2)

    log.info(f"Status JSON written to {STATUS_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
