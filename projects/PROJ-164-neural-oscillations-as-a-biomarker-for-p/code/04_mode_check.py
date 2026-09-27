import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path to allow relative imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_setup import get_logger, log_mode_switch
from utils.io_helpers import load_json

logger = get_logger(__name__)

MANIFEST_PATH = Path("data/processed/verified_source_manifest.json")
STATE_FILE = Path("state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml")
MODE_FLAG_PATH = Path("state/projects/mode_flag.json")

def load_manifest() -> dict:
    """Load the verified source manifest."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found at {MANIFEST_PATH}. "
            "Please run T011 (Source Verification) first."
        )
    return load_json(MANIFEST_PATH)

def determine_mode(manifest: dict) -> str:
    """
    Determine the pipeline mode based on the manifest.
    
    Returns:
        str: 'Primary', 'Data Insufficient', or 'Underpowered'
    """
    status = manifest.get("status", "unknown")
    n_actual = manifest.get("N_actual", 0)
    
    if status == "absent":
        return "Data Insufficient"
    
    # Check for power analysis results if available in manifest or separate file
    # T009 updates the manifest or we can check for a power analysis report
    # For this task, we assume T009 might have updated the manifest with N_min
    n_min = manifest.get("N_min", None)
    
    if n_min is not None and n_actual is not None:
        if n_actual < n_min:
            return "Underpowered"
    
    # If status is 'found' and power check passes (or isn't applicable yet)
    if status == "found":
        return "Primary"
    
    return "Data Insufficient"

def save_mode_flag(mode: str) -> None:
    """Save the determined mode flag to the state directory."""
    MODE_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    mode_data = {
        "mode": mode,
        "source": str(MANIFEST_PATH),
        "message": f"Mode set to {mode} based on verified_source_manifest.json"
    }
    
    with open(MODE_FLAG_PATH, 'w') as f:
        json.dump(mode_data, f, indent=2)
    
    logger.info(f"Mode flag saved to {MODE_FLAG_PATH}: {mode}")

def main():
    """
    T012: Mode Propagation Task.
    
    Reads verified_source_manifest.json and sets the global mode_flag variable
    for downstream tasks. If mode is 'Data Insufficient' or 'Underpowered',
    downstream tasks will skip execution.
    
    This task does NOT terminate the pipeline; it simply sets the flag.
    """
    try:
        logger.info("Starting T012: Mode Propagation Task")
        
        # Load manifest
        manifest = load_manifest()
        logger.info(f"Loaded manifest from {MANIFEST_PATH}")
        logger.debug(f"Manifest content: {json.dumps(manifest, indent=2)}")
        
        # Determine mode
        mode = determine_mode(manifest)
        
        # Log the mode switch
        log_mode_switch(mode)
        
        # Save the mode flag
        save_mode_flag(mode)
        
        # Log the outcome
        if mode in ["Data Insufficient", "Underpowered"]:
            reason = "No single-source paired dataset found" if mode == "Data Insufficient" else "Insufficient sample size for power"
            logger.warning(f"Pipeline mode set to '{mode}'. Downstream tasks will skip execution. Reason: {reason}")
        else:
            logger.info(f"Pipeline mode set to '{mode}'. Downstream tasks will execute.")
        
        logger.info("T012 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during mode propagation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
