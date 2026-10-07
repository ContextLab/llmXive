"""
Verification script for T004b: Verify checkpointing functionality.
Creates a checkpoint, loads it, and validates the JSON structure.
"""
import os
import json
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.utils.checkpointing import save_state, load_state, get_checkpoint_path, ensure_checkpoint_dir, delete_checkpoint
from code.utils.logging_config import setup_pipeline_logger

def main():
    """
    Executes the verification logic for T004b.
    1. Ensures the checkpoint directory exists.
    2. Saves a state with required keys: current_dataset_id, last_seed, error_counts.
    3. Loads the state back.
    4. Verifies the loaded JSON contains the required keys and valid data types.
    5. Prints success or failure status.
    """
    # Initialize logger
    logger = setup_pipeline_logger()
    run_id = "verify_t004b_run"

    logger.info(f"Starting checkpoint verification for run_id={run_id}")

    # 1. Ensure directory exists
    checkpoint_dir = ensure_checkpoint_dir()
    logger.info(f"Checkpoint directory ensured at: {checkpoint_dir}")

    # 2. Prepare test data matching the spec requirements
    test_data = {
        "current_dataset_id": "dataset_uci_001",
        "last_seed": 42,
        "error_counts": {
            "download_error": 0,
            "filter_error": 2
        }
    }

    # 3. Save state
    save_success = save_state(run_id, "initialization", test_data)
    if not save_success:
        logger.error("Failed to save checkpoint. Verification FAILED.")
        return 1

    # 4. Load state
    loaded_state = load_state(run_id)
    if loaded_state is None:
        logger.error("Failed to load checkpoint. Verification FAILED.")
        return 1

    # 5. Verify JSON structure and content
    required_keys = ["current_dataset_id", "last_seed", "error_counts"]
    missing_keys = [key for key in required_keys if key not in loaded_state]

    if missing_keys:
        logger.error(f"Checkpoint missing required keys: {missing_keys}. Verification FAILED.")
        return 1

    # Validate types
    if not isinstance(loaded_state["current_dataset_id"], str):
        logger.error("current_dataset_id must be a string.")
        return 1

    if not isinstance(loaded_state["last_seed"], int):
        logger.error("last_seed must be an integer.")
        return 1

    if not isinstance(loaded_state["error_counts"], dict):
        logger.error("error_counts must be a dictionary.")
        return 1

    # Verify specific values match what was saved
    if loaded_state["current_dataset_id"] != test_data["current_dataset_id"]:
        logger.error("current_dataset_id mismatch.")
        return 1

    if loaded_state["last_seed"] != test_data["last_seed"]:
        logger.error("last_seed mismatch.")
        return 1

    if loaded_state["error_counts"] != test_data["error_counts"]:
        logger.error("error_counts mismatch.")
        return 1

    # Verify the file exists on disk and is valid JSON
    checkpoint_path = get_checkpoint_path(run_id)
    if not checkpoint_path.exists():
        logger.error(f"Checkpoint file does not exist at {checkpoint_path}. Verification FAILED.")
        return 1

    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            disk_content = json.load(f)
        if not isinstance(disk_content, dict):
            logger.error("Disk checkpoint is not a valid JSON object.")
            return 1
    except json.JSONDecodeError as e:
        logger.error(f"Disk checkpoint is not valid JSON: {e}. Verification FAILED.")
        return 1

    logger.info("All verification checks passed. Checkpointing is working correctly.")
    logger.info(f"Checkpoint file location: {checkpoint_path}")
    
    # Cleanup for idempotency (optional, but good practice for verification scripts)
    delete_checkpoint(run_id)
    logger.info(f"Cleaned up test checkpoint: {run_id}")

    return 0

if __name__ == "__main__":
    sys.exit(main())