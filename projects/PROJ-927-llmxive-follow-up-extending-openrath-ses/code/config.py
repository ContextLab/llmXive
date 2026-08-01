import os
import json
from pathlib import Path

# Configuration constants
SEED = 42
CORRUPTION_RATE = 0.1
WORKFLOW_COUNT = 500
SWEEP_RATES = [0.05, 0.10, 0.20]

# Directory paths
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "workflows"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
STATE_DIR = BASE_DIR / "state"
PROJECT_STATE_FILE = STATE_DIR / "projects" / "PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"

def ensure_directories():
    """Create necessary directories if they don't exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR / "event_log",
        PROCESSED_DATA_DIR / "session_first",
        PROCESSED_DATA_DIR / "results",
        STATE_DIR,
        STATE_DIR / "projects"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def load_state():
    """Load project state from YAML file."""
    if not PROJECT_STATE_FILE.exists():
        return {"checkpoint": {}, "artifact_hashes": {}}
    
    # Simple YAML loader (assuming no complex YAML features needed yet)
    # In production, use PyYAML
    state = {}
    with open(PROJECT_STATE_FILE, "r") as f:
        content = f.read()
        # Very basic parsing for checkpoint and artifact_hashes
        # This is a placeholder; proper YAML parsing should be implemented
        if "checkpoint:" in content:
            state["checkpoint"] = {}
        if "artifact_hashes:" in content:
            state["artifact_hashes"] = {}
    return state

def save_state(state):
    """Save project state to YAML file."""
    PROJECT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROJECT_STATE_FILE, "w") as f:
        # Simple YAML serialization
        f.write("checkpoint:\n")
        for k, v in state.get("checkpoint", {}).items():
            f.write(f"  {k}: {v}\n")
        f.write("artifact_hashes:\n")
        for k, v in state.get("artifact_hashes", {}).items():
            f.write(f"  {k}: {v}\n")
