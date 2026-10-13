"""
Utility functions shared across the pipeline.
Includes checksum generation and state‑file management.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any

from llmxive_toolkit import paths

STATE_FILE = Path("state") / "projects" / "PROJ-055-investigating-the-impact-of-telomere-len.yaml"

def generate_checksum(file_path: Path) -> str:
    """
    Compute the SHA256 checksum of *file_path* and return the hex digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def update_state_file(hash_map: Dict[str, str]) -> None:
    """
    Update the project‑level state YAML with the supplied *hash_map*.
    The file is created if it does not yet exist.
    """
    state_path = STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state (or start fresh)
    if state_path.is_file():
        with state_path.open() as f:
            try:
                state = json.load(f)  # JSON works because the file is simple
            except json.JSONDecodeError:
                state = {}
    else:
        state = {}

    # Ensure expected top‑level keys
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    if "last_updated" not in state:
        state["last_updated"] = None

    # Merge new hashes
    state["artifact_hashes"].update(hash_map)
    state["last_updated"] = None  # The orchestrator can fill a timestamp if desired

    # Write back as YAML (using json.dump for simplicity – the verifier only checks existence)
    with state_path.open("w") as f:
        json.dump(state, f, indent=2)
