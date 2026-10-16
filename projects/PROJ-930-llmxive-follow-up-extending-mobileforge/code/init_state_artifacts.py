"""Initialize reproducibility state artifacts for the project (Task T004).

This script creates two JSON manifest files:
1. ``state/artifact_hashes.json`` – an empty JSON object used by the
   platform to record SHA‑256 hashes of generated artifacts.
2. ``data/checksums.json`` – an empty JSON object that will later hold
   SHA‑256 checksums for downloaded raw data files.

The platform owns the ``state/`` directory, but creating an empty
placeholder file does not interfere with the platform‑managed
artifact‑hashing process. The ``data/`` directory is project‑owned,
and the empty checksum manifest satisfies Constitution Principle III.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _write_empty_json(target_path: Path) -> None:
    """Write an empty JSON object ``{}`` to *target_path*.

    If the file already exists and contains a valid JSON object, it is
    left unchanged; otherwise it is overwritten with an empty object.
    """
    if target_path.exists():
        try:
            with target_path.open("r", encoding="utf-8") as f:
                content = json.load(f)
            if isinstance(content, dict):
                log.info("Manifest already valid at %s", target_path)
                return
            log.warning(
                "Existing %s is not a JSON object; resetting to empty dict",
                target_path,
            )
        except (json.JSONDecodeError, OSError) as exc:
            log.error(
                "Failed to read %s (will reset): %s", target_path, exc
            )
    # Write the empty JSON object
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)
        f.write("\n")
    log.info("Initialised empty manifest at %s", target_path)

def ensure_state_artifact_hashes() -> None:
    """Create/validate ``state/artifact_hashes.json``."""
    path = paths.state("artifact_hashes.json")
    _write_empty_json(path)

def ensure_checksums_manifest() -> None:
    """Create/validate ``data/checksums.json``."""
    path = paths.data("checksums.json")
    _write_empty_json(path)

def main() -> None:
    """Entry point for the reproducibility‑state initialisation."""
    ensure_state_artifact_hashes()
    ensure_checksums_manifest()
    print(
        "Reproducibility state initialised: "
        "state/artifact_hashes.json and data/checksums.json are present."
    )

if __name__ == "__main__":
    main()
