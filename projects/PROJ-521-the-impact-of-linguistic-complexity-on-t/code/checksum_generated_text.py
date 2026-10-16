"""
checksum_generated_text.py

This script computes a SHA-256 checksum for the generated text CSV
(`data/raw/generated_text.csv`) and records the checksum in the project
state file (`state/projects/PROJ-521-the-impact-of-linguistic-complexity-on-t.yaml`).

It is intended to be run after `generate_text.py` completes successfully.
"""

import datetime
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Import helper functions from the existing update_state module
from update_state import compute_sha256, load_state, save_state

log = get_logger(__name__)

def main() -> int:
    """
    Main entry point.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    # Locate the generated CSV file
    csv_path: Path = paths.data("raw", "generated_text.csv")
    if not csv_path.is_file():
        log.error("Generated text CSV not found at %s", csv_path)
        raise FileNotFoundError(f"Generated text CSV not found at {csv_path}")

    # Compute SHA‑256 checksum
    checksum: str = compute_sha256(csv_path)
    log.info("Checksum for %s: %s", csv_path.name, checksum)

    # Load the state YAML file
    state_path: Path = paths.path(
        "state", "projects", "PROJ-521-the-impact-of-linguistic-complexity-on-t.yaml"
    )
    state: dict = load_state(state_path)

    # Update checksum entry
    data_checksums: dict = state.get("data_checksums", {})
    data_checksums[csv_path.name] = checksum
    state["data_checksums"] = data_checksums

    # Record the timestamp of this update
    state["last_updated"] = datetime.datetime.utcnow().isoformat()

    # Persist the updated state
    save_state(state_path, state)
    log.info("State file updated at %s", state_path)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())