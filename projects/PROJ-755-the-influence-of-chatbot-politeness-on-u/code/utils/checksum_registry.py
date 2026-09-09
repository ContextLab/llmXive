import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from .data_integrity import compute_file_checksum

PROJECT_ID = "PROJ-755-the-influence-of-chatbot-politeness-on-u"
STATE_DIR = Path("state/projects")
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

def ensure_state_directory():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_state() -> Dict[str, Any]:
    """Load the existing state file or return a default structure."""
    ensure_state_directory()
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": PROJECT_ID,
        "artifact_hashes": {
            "raw_data": {}
        },
        "metadata": {
            "created": None,
            "updated": None
        }
    }

def save_state(state: Dict[str, Any]) -> None:
    """Save the state dictionary to the YAML file."""
    ensure_state_directory()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def register_raw_data_checksum(source_name: str, file_path: str) -> str:
    """
    Compute the checksum for a raw data file and register it in the state.
    
    Args:
        source_name: The logical name of the dataset (e.g., 'hci_p2', 'persona_chat').
        file_path: The absolute or relative path to the raw data file.
    
    Returns:
        The computed SHA-256 checksum string.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    
    checksum = compute_file_checksum(path)
    
    state = load_state()
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {"raw_data": {}}
    if "raw_data" not in state["artifact_hashes"]:
        state["artifact_hashes"]["raw_data"] = {}
    
    state["artifact_hashes"]["raw_data"][source_name] = {
        "checksum": checksum,
        "file_path": str(path),
        "size_bytes": path.stat().st_size
    }
    
    # Update timestamp
    import datetime
    state["metadata"]["updated"] = datetime.datetime.now().isoformat()
    
    save_state(state)
    return checksum

def get_raw_data_checksums() -> Dict[str, Any]:
    """Retrieve all registered raw data checksums."""
    state = load_state()
    return state.get("artifact_hashes", {}).get("raw_data", {})

def main():
    """
    CLI entry point to register a checksum.
    Usage: python -m code.utils.checksum_registry register <source_name> <file_path>
    """
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.checksum_registry register <source_name> <file_path>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "register":
        if len(sys.argv) != 4:
            print("Usage: python -m code.utils.checksum_registry register <source_name> <file_path>")
            sys.exit(1)
        source_name = sys.argv[2]
        file_path = sys.argv[3]
        try:
            checksum = register_raw_data_checksum(source_name, file_path)
            print(f"Registered {source_name}: {checksum}")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif action == "show":
        checksums = get_raw_data_checksums()
        print(json.dumps(checksums, indent=2))
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
