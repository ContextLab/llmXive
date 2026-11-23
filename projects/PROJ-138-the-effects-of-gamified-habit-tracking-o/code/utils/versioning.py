import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("versioning")

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict:
    """Load state.yaml if it exists."""
    state_path = "state.yaml"
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {"artifacts": {}}

def save_state(state: Dict):
    """Save state to state.yaml."""
    state_path = "state.yaml"
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def update_artifact_state(file_path: str, state: Dict):
    """Update state with artifact hash."""
    if not os.path.exists(file_path):
        return
    
    artifact_name = os.path.relpath(file_path, start=".")
    file_hash = calculate_sha256(file_path)
    
    state["artifacts"][artifact_name] = {
        "hash": file_hash,
        "updated": datetime.now().isoformat()
    }

def hash_all_final_artifacts():
    """Hash all final artifacts and update state."""
    state = load_state()
    
    final_artifacts = [
        "data/processed/merged_data.csv",
        "data/processed/psychometrics.json",
        "data/processed/model_intercept_results.json",
        "data/processed/robustness_report.json",
        "data/reports/final_analysis.html",
        "data/raw/synthetic_data.csv",
        "data/raw/synthetic_data_marker.json"
    ]
    
    for artifact in final_artifacts:
        update_artifact_state(artifact, state)
    
    save_state(state)
    logger.info("Updated state.yaml with artifact hashes.")

def main():
    parser = argparse.ArgumentParser(description="Versioning and hashing")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Versioning")
    
    try:
        hash_all_final_artifacts()
        log_pipeline_stage(logger, "SUCCESS", "Versioning Complete")
        return 0
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
  import argparse
  sys.exit(main())