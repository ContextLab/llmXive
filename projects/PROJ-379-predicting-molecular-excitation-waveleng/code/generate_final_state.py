"""
Generate the final state YAML file for project PROJ-379-predicting-molecular-excitation-waveleng.

This script computes SHA256 hashes for all key artifacts produced during the pipeline
(ingestion, splitting, model training, evaluation, attribution, sensitivity) and writes
them to the project state file.

It relies on the `hash_artifacts` module which is already part of the project.
"""
import os
import sys
import logging
from pathlib import Path

# Import the existing hash_artifacts module functionality
# The API surface confirms: from hash_artifacts import compute_file_hash, collect_artifacts, update_state_file, main
from hash_artifacts import collect_artifacts, update_state_file

# Setup logging similar to other code modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_ID = "PROJ-379-predicting-molecular-excitation-waveleng"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

# Define the artifacts to hash based on the pipeline outputs defined in tasks.md
# These are the expected outputs from the completed tasks (T008, T010, T015, T016, T024, T026, etc.)
ARTIFACT_PATTERNS = [
    "data/processed/cleaned.csv",
    "data/processed/split_indices.json",
    "data/processed/train_val_test.csv",
    "data/processed/power_analysis.json",
    "data/processed/collinearity_flags.json",
    "data/processed/redundancy_masks.json",
    "data/processed/model.pt",
    "data/processed/metrics_partial.json",
    "data/processed/evaluation_narrative.md",
    "data/processed/raw_attribution.json",
    "data/processed/masked_attribution.json",
    "data/processed/sensitivity_report.csv",
    "data/processed/sensitivity_report.md",
    "data/processed/timing.json",
    "data/processed/sampling_log.json",
    "data/processed/verification_gate.log",
    "data/processed/metrics.json",  # Output from T044/T027
    "code/ingest.py",
    "code/split.py",
    "code/model.py",
    "code/train.py",
    "code/evaluate.py",
    "code/explain.py",
    "code/sensitivity.py",
    "code/analyze_results.py",
    "code/hash_artifacts.py",
]

def main():
    logger.info(f"Starting final state generation for project: {PROJECT_ID}")
    
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created state directory: {STATE_DIR}")

    # Collect artifacts and compute hashes using the existing utility
    # We pass the relative patterns to collect_artifacts which handles globbing
    try:
        artifacts_dict = collect_artifacts(ARTIFACT_PATTERNS, base_dir=PROJECT_ROOT)
        
        if not artifacts_dict:
            logger.warning("No artifacts found to hash. Check if data/processed and code/ contain expected files.")
            # We still proceed to write the state file, even if empty, to satisfy the task requirement of generating it.
        
        update_state_file(
            state_path=STATE_FILE,
            artifact_hashes=artifacts_dict,
            project_id=PROJECT_ID
        )
        
        logger.info(f"Successfully updated state file: {STATE_FILE}")
        logger.info(f"Total artifacts hashed: {len(artifacts_dict)}")
        
        # Print a summary of what was hashed for the user
        logger.info("Hashed artifacts:")
        for path, hash_val in artifacts_dict.items():
            logger.info(f"  {path}: {hash_val[:16]}...")

    except Exception as e:
        logger.error(f"Failed to generate final state: {e}")
        raise

if __name__ == "__main__":
    main()