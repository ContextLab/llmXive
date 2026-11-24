"""Task T008: initialize the pipeline logging infrastructure.

Configures stdout + rotating-file logging (logs/pipeline.log), logs the
current pipeline mode from the verified source manifest, and records a
resource-usage snapshot as evidence that the infrastructure works.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running both as `python code/08_logging_setup.py` and as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.logging_setup import (
    get_logger,
    log_mode_switch,
    log_resource_usage,
    utc_timestamp,
)


def main() -> int:
    log = get_logger("setup")

    log.info("=== PROJ-164 pipeline logging infrastructure (T008) ===")
    log.info("Timestamp: %s", utc_timestamp())

    # Record the current pipeline mode as a mode-switch evidence entry.
    manifest_candidates = [
        Path(__file__).resolve().parents[1] / "data" / "verified_source_manifest.json",
        Path(__file__).resolve().parents[1] / "data" / "processed" / "verified_source_manifest.json",
    ]
    mode = "unknown"
    for manifest_path in manifest_candidates:
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as fh:
                    manifest = json.load(fh)
                mode = manifest.get("mode_flag", "unknown")
                log.info("Manifest loaded from %s", manifest_path)
                break
            except (OSError, json.JSONDecodeError) as exc:
                log.warning("Could not read manifest %s: %s", manifest_path, exc)
    if mode == "unknown":
        log.warning("No verified source manifest found; mode unknown")

    log_mode_switch(log, "startup", mode,
                    reason="Pipeline start; mode read from verified source manifest")

    log_resource_usage(log, context="logging setup")

    log.info("Logging infrastructure ready: stdout + logs/pipeline.log "
             "(RotatingFileHandler, 5 MB x 3 backups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
