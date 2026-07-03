import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

STATE_DIR = Path("state/projects")
PROJECT_ID = "PROJ-442-predicting-molecular-reactivity-using-ma"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

def ensure_state_dir():
    """Ensure state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_checksum(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_state() -> Dict[str, Any]:
    """Load state from YAML file."""
    ensure_state_dir()
    if not STATE_FILE.exists():
        return {
            "project_id": PROJECT_ID,
            "artifacts": {},
            "pipeline_status": "initialized",
            "last_updated": datetime.utcnow().isoformat()
        }
    with open(STATE_FILE, 'r') as f:
        return yaml.safe_load(f)

def save_state(state: Dict[str, Any]):
    """Save state to YAML file."""
    ensure_state_dir()
    state["last_updated"] = datetime.utcnow().isoformat()
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def update_artifact_state(artifact_name: str, path: str, checksum: str, metadata: Optional[Dict[str, Any]] = None):
    """Update artifact state in the project state file."""
    state = load_state()
    state["artifacts"][artifact_name] = {
        "path": path,
        "checksum": checksum,
        "metadata": metadata or {},
        "updated_at": datetime.utcnow().isoformat()
    }
    save_state(state)

def update_pipeline_status(status: str):
    """Update pipeline status in the state file."""
    state = load_state()
    state["pipeline_status"] = status
    state["last_updated"] = datetime.utcnow().isoformat()
    save_state(state)
