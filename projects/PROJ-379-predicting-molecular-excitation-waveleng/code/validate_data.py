"""
T009: Data Validity Gate Implementation

Logic:
1. Read data/processed/cleaned.csv (produced by T008).
2. Check if 'lambda_max' values are purely computed (no experimental source flag) 
   OR if the dataset is entirely synthetic/fake (which should have been prevented by T008).
3. If ONLY computed values exist (and no experimental ground truth is available):
   - Reframe SC-001: Update state YAML to set sc001_status = "computed_ground_truth".
   - Log the reframing message.
   - Exit with code 0 (do not halt the pipeline).
4. If experimental data exists, proceed normally (SC-001 remains active).
5. If the dataset is empty or invalid, raise an error.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/validate_data.log')
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-379-predicting-molecular-excitation-waveleng.yaml"
CLEANED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned.csv"
LOG_MESSAGE = "SC-001 reframed: Experimental noise floor assumption invalid. Success criteria now based on computed ground truth."

def load_state_file(path: Path) -> Dict[str, Any]:
    """Load the project state YAML file."""
    if not path.exists():
        logger.warning(f"State file not found at {path}. Creating new structure.")
        return {"artifact_hashes": {}, "updated_at": None, "sc001_status": "pending"}
    
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {"artifact_hashes": {}, "updated_at": None, "sc001_status": "pending"}
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {"artifact_hashes": {}, "updated_at": None, "sc001_status": "pending"}

def save_state_file(path: Path, data: Dict[str, Any]) -> None:
    """Save the project state YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    logger.info(f"State file updated at {path}")

def validate_data() -> bool:
    """
    Main validation logic for T009.
    Returns True if validation passes (or is reframed), False otherwise.
    """
    logger.info("Starting T009: Data Validity Gate")
    
    if not CLEANED_DATA_PATH.exists():
        logger.error(f"Cleaned data file not found at {CLEANED_DATA_PATH}. "
                     "Please ensure T008 (ingest.py) has run successfully.")
        return False

    try:
        df = pd.read_csv(CLEANED_DATA_PATH)
    except Exception as e:
        logger.error(f"Failed to read cleaned data: {e}")
        return False

    if df.empty:
        logger.error("Cleaned data is empty. Cannot proceed with validation.")
        return False

    # Check for 'lambda_max' column
    if 'lambda_max' not in df.columns:
        logger.error("Missing 'lambda_max' column in cleaned data.")
        return False

    # Check for source indicators (e.g., 'source_type', 'is_computed', etc.)
    # If the dataset lacks experimental source flags, we assume it's computed-only
    # based on the task description: "If only computed lambda_max values exist (no experimental)"
    source_cols = [col for col in df.columns if 'source' in col.lower() or 'experimental' in col.lower()]
    
    is_computed_only = False
    
    if not source_cols:
        # No source columns found -> assume computed-only (or synthetic, but T008 should prevent synthetic)
        logger.warning("No source type columns found in dataset. Assuming computed-only ground truth.")
        is_computed_only = True
    else:
        # Check if all entries are marked as computed
        for col in source_cols:
            if df[col].dtype == 'object':
                unique_vals = df[col].unique()
                if all(v in ['computed', 'calculated', 'theoretical'] for v in unique_vals if pd.notna(v)):
                    is_computed_only = True
                    logger.info(f"All values in '{col}' indicate computed ground truth.")
                    break
            elif df[col].dtype == 'bool':
                if df[col].all(): # Assuming True means computed
                    is_computed_only = True
                    logger.info(f"All values in '{col}' indicate computed ground truth.")
                    break

    if is_computed_only:
        logger.warning(LOG_MESSAGE)
        
        # Update state file
        state = load_state_file(STATE_FILE)
        state['sc001_status'] = "computed_ground_truth"
        state['updated_at'] = pd.Timestamp.now().isoformat()
        save_state_file(STATE_FILE, state)
        
        logger.info("State updated: sc001_status set to 'computed_ground_truth'")
        return True
    else:
        logger.info("Experimental ground truth detected. SC-001 remains active.")
        return True

def main():
    """Entry point for the script."""
    success = validate_data()
    if success:
        logger.info("T009 validation passed.")
        sys.exit(0)
    else:
        logger.error("T009 validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()