import hashlib
import os
import yaml
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import load_config

logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_relative_path(file_path: str, base_path: str) -> str:
    """Get relative path from base path."""
    return os.path.relpath(file_path, base_path)

def find_state_file(project_id: str) -> Path:
    """Find the state file for a project."""
    state_dir = Path("state/projects")
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"{project_id}.yaml"

def load_state(state_file: Path) -> Dict[str, Any]:
    """Load state file."""
    if not state_file.exists():
        return {"project_id": state_file.stem, "updated_at": "", "artifact_hashes": {}}
    with open(state_file, "r") as f:
        return yaml.safe_load(f)

def save_state(state_file: Path, state: Dict[str, Any]) -> None:
    """Save state file."""
    state["updated_at"] = datetime.utcnow().isoformat() + "Z"
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def process_data_directory(data_dir: str, state: Dict[str, Any]) -> None:
    """Process data directory and update artifact hashes."""
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory {data_dir} does not exist.")
        return

    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith((".pyc", ".pyo", ".yaml")):
                continue
            file_path = os.path.join(root, file)
            rel_path = get_relative_path(file_path, "data")
            file_hash = compute_sha256(file_path)
            state["artifact_hashes"][rel_path] = file_hash

def audit_data_integrity(state: Dict[str, Any]) -> bool:
    """Audit data integrity by comparing stored hashes with current hashes."""
    data_dir = "data"
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory {data_dir} does not exist.")
        return True

    all_valid = True
    for rel_path, stored_hash in state.get("artifact_hashes", {}).items():
        file_path = os.path.join(data_dir, rel_path)
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} missing from disk.")
            all_valid = False
            continue
        current_hash = compute_sha256(file_path)
        if current_hash != stored_hash:
            logger.warning(f"Hash mismatch for {file_path}: stored={stored_hash}, current={current_hash}")
            all_valid = False
    return all_valid

def update_state_file(project_id: str, data_dir: str = "data") -> None:
    """Update state file with current artifact hashes."""
    state_file = find_state_file(project_id)
    state = load_state(state_file)
    state["project_id"] = project_id
    process_data_directory(data_dir, state)
    save_state(state_file, state)
    logger.info(f"State file updated: {state_file}")

def generate_reproducibility_audit(project_id: str) -> None:
    """
    Generate a reproducibility audit file containing:
    - git commit hash
    - requirements.txt hash
    - python version
    
    Output: state/projects/{project_id}-reproducibility.yaml
    """
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    repro_file = state_dir / f"{project_id}-reproducibility.yaml"

    # 1. Get Git Commit Hash
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Git repository not found or 'git' command unavailable. Setting git_hash to 'unknown'.")
        git_hash = "unknown"

    # 2. Get Requirements.txt Hash
    req_path = Path("requirements.txt")
    if req_path.exists():
        req_hash = compute_sha256(str(req_path))
    else:
        logger.warning("requirements.txt not found. Setting requirements_hash to 'missing'.")
        req_hash = "missing"

    # 3. Get Python Version
    python_version = sys.version

    audit_data = {
        "project_id": project_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "git_hash": git_hash,
        "requirements_hash": req_hash,
        "python_version": python_version
    }

    with open(repro_file, "w") as f:
        yaml.dump(audit_data, f, default_flow_style=False)

    logger.info(f"Reproducibility audit generated: {repro_file}")

def main():
    """Main entry point for hygiene operations."""
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    project_id = config.get("project_id", "PROJ-163-exploring-the-role-of-network-structure-")

    if len(sys.argv) > 1 and sys.argv[1] == "--reproducibility":
        generate_reproducibility_audit(project_id)
    else:
        update_state_file(project_id)
        if not audit_data_integrity(load_state(find_state_file(project_id))):
            logger.error("Data integrity audit failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()