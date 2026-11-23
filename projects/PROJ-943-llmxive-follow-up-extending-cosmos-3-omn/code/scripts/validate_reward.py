"""
T018: Validate the existence of 'physics_reward' in the Bridge Data source.

This script checks the real dataset for the presence of the 'physics_reward' field.
If the field is missing, it aborts with a clear error (no proxy fallback).
"""
import sys
import json
from pathlib import Path
from datasets import load_dataset
from utils.logger import get_logger, log_script_start, log_script_end

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = get_logger(__name__)

def check_physics_reward_exists(dataset_name: str = "bridge-to-worlds/bridge-data", sample_size: int = 1000) -> bool:
    """
    Loads a sample of the real dataset to verify 'physics_reward' exists.
    
    Args:
        dataset_name: HuggingFace dataset identifier.
        sample_size: Number of rows to scan for the field.
        
    Returns:
        True if 'physics_reward' is found in the schema/sample.
        
    Raises:
        RuntimeError: If the field is missing or dataset fetch fails.
    """
    logger.info(f"Fetching real data from {dataset_name} to validate 'physics_reward' presence...")
    
    try:
        # Use streaming to avoid loading full dataset into memory
        ds = load_dataset(dataset_name, split="train", streaming=True)
        
        found = False
        count = 0
        
        for item in ds:
            if "physics_reward" in item:
                found = True
                break
            count += 1
            if count >= sample_size:
                break
        
        if not found:
            raise RuntimeError(
                f"CRITICAL: 'physics_reward' field NOT found in the first {count} samples of {dataset_name}. "
                "The downstream evaluation (T017) requires this native continuous reward signal. "
                "Aborting execution as per T018 constraints (no proxy fallback)."
            )
        
        logger.info(f"SUCCESS: 'physics_reward' field verified in {dataset_name}.")
        return True

    except Exception as e:
        # Re-raise to fail loudly
        logger.error(f"Failed to validate data source: {e}")
        raise

def main():
    log_script_start("T018-validate-reward")
    try:
        check_physics_reward_exists()
        logger.info("Validation passed. Pipeline can proceed.")
    except RuntimeError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(1)
    finally:
        log_script_end("T018-validate-reward")

if __name__ == "__main__":
    main()