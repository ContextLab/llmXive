"""
Versioning and artifact hashing module.
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("versioning")

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_path: str = "state.yaml") -> Dict:
    """Load state file."""
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {"artifacts": {}, "last_updated": None}

def save_state(state: Dict, state_path: str = "state.yaml"):
    """Save state file."""
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def update_artifact_state(state: Dict, name: str, path: str):
    """Update artifact state in the dictionary."""
    if "artifacts" not in state:
        state["artifacts"] = {}
    state["artifacts"][name] = {
        "path": path,
        "hash": calculate_sha256(path),
        "timestamp": datetime.now().isoformat()
    }

def hash_all_final_artifacts():
    """Hash all final artifacts and update state."""
    root = Path(__file__).parent.parent.parent
    state_path = root / "state.yaml"
    
    artifacts_to_hash = [
        ("merged_data", "data/processed/merged_data.csv"),
        ("psychometrics", "data/processed/psychometrics.json"),
        ("model_summary", "data/processed/model_summary.txt"),
        ("final_report", "data/reports/final_analysis.html"),
    ]
    
    state = load_state(str(state_path))
    state["last_updated"] = datetime.now().isoformat()
    
    for name, rel_path in artifacts_to_hash:
        full_path = root / rel_path
        if full_path.exists():
            update_artifact_state(state, name, rel_path)
            logger.info(f"Hashed {name}: {calculate_sha256(str(full_path))[:16]}...")
        else:
            logger.warning(f"Artifact not found: {full_path}")
    
    save_state(state, str(state_path))
    logger.info("State file updated.")

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["hash"], default="hash")
    args = parser.parse_args()
    
    if args.action == "hash":
        hash_all_final_artifacts()

if __name__ == "__main__":
    main()