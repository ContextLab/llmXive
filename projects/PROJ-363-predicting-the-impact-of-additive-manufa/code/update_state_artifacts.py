import os
import sys
import logging
import hashlib
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import load_state, update_state, compute_file_hash, setup_logging

logger = setup_logging()

def main():
    """
    T036: Update state.yaml with hashes of plots and statistical reports.
    
    This script scans the results directory for generated artifacts from US3
    (SHAP plots, significance reports) and updates state.yaml with their
    SHA-256 hashes.
    """
    state_path = project_root / "state.yaml"
    
    if not state_path.exists():
        logger.error("state.yaml not found at %s", state_path)
        sys.exit(1)
    
    # Load current state
    state = load_state(state_path)
    
    # Define artifacts to hash
    artifacts_to_hash = {
        "shap_summary_plot": "results/plots/shap_summary.png",
        "significance_report": "results/reports/significance_report.json"
    }
    
    updated = False
    for key, rel_path in artifacts_to_hash.items():
        full_path = project_root / rel_path
        
        if not full_path.exists():
            logger.warning("Artifact not found: %s (skipping)", rel_path)
            continue
        
        file_hash = compute_file_hash(str(full_path))
        
        # Update state if hash changed or key doesn't exist
        current_hash = state.get("artifacts", {}).get(key)
        if current_hash != file_hash:
            if "artifacts" not in state:
                state["artifacts"] = {}
            state["artifacts"][key] = file_hash
            updated = True
            logger.info("Updated state: %s -> %s", key, file_hash[:16] + "...")
    
    if updated:
        update_state(state_path, state)
        logger.info("state.yaml updated successfully")
    else:
        logger.info("No state updates needed")

if __name__ == "__main__":
    main()