"""
Runtime source enforcement to ensure single canonical source per run.
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-169-predicting-the-elastic-moduli-of-2d-mate"
SOURCE_STATE_FILE = PROJECT_ROOT / "data" / ".source_state"

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_active_source() -> Optional[str]:
    """Get the active source from the state file."""
    if SOURCE_STATE_FILE.exists():
        try:
            with open(SOURCE_STATE_FILE, "r") as f:
                state = json.load(f)
            return state.get("active_source")
        except (json.JSONDecodeError, IOError) as e:
            raise RuntimeError(f"Error reading source state: {e}")
    return None

def persist_source(source: str) -> None:
    """Persist the source identity to the state file."""
    SOURCE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {"active_source": source}
    with open(SOURCE_STATE_FILE, "w") as f:
        json.dump(state, f)

def enforce_single_source(source: str) -> None:
    """
    Enforce that only one data source is active per run.
    Checks the state file and raises an error if there's a mismatch.
    """
    # Check if a source is already active
    active_source = get_active_source()
    
    if active_source is not None and active_source != source:
        error_msg = f"Source mismatch: State file indicates {active_source}, but DATA_SOURCE={source}"
        print(error_msg, file=sys.stderr)
        raise SystemExit(1)
    
    # If no source is active, persist the current one
    if active_source is None:
        persist_source(source)
        logging.info(f"Source {source} persisted.")
    else:
        logging.info(f"Source {source} is already active.")

def reset_source_lock() -> None:
    """Reset the source lock (for testing or cleanup)."""
    if SOURCE_STATE_FILE.exists():
        SOURCE_STATE_FILE.unlink()

# Import logging here to avoid circular import if needed
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Example usage for testing
    source = os.getenv("DATA_SOURCE", "materials_project")
    try:
        enforce_single_source(source)
        print(f"Source {source} enforced.")
    except SystemExit:
        print("Source enforcement failed.")
        sys.exit(1)
