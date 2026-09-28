import os
import sys
import logging
from pathlib import Path
import yaml

# Ensure code directory is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_data_source_config():
    """
    Read the dataset ID/URL from code/config/data_sources.yaml.
    If missing, raise RuntimeError.
    If present, attempt to verify (fetch or local check).
    """
    logger = logging.getLogger("verify_source")
    config_path = Path("code/config/data_sources.yaml")

    if not config_path.exists():
        raise RuntimeError("E-NO-SOURCE-CONFIG: Configuration missing. Aborting.")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise RuntimeError(f"E-NO-SOURCE-CONFIG: Invalid YAML in config. {e}")

    dataset_id = config.get("dataset_id")
    verified = config.get("verified", False)

    if not dataset_id:
        raise RuntimeError("E-NO-SOURCE-CONFIG: Dataset ID missing. Aborting.")

    # Check if local file exists as a fallback for verification if network fails
    local_path = Path("data/raw/cyberbullying_2021.csv")
    
    if not verified:
        logger.warning(f"Source not marked as verified in config. Attempting fetch check for {dataset_id}...")
        # Attempt a quick fetch or check to verify existence
        # We don't download the whole thing here, just check if we can access it
        # For simplicity, we assume if it's in config and we can import the library, it's likely valid
        # A more robust check would try a head request or load a small slice
        try:
            from datasets import load_dataset
            # Try to get info without loading full data
            ds = load_dataset(dataset_id, split="train", streaming=True)
            next(iter(ds)) # Just peek
            logger.info("Source verified (streaming check passed).")
        except Exception as e:
            if local_path.exists():
                logger.info("Source verified (local file exists).")
            else:
                raise RuntimeError(f"E-NO-REAL-SOURCE-001: Real data source not found. Aborting. Error: {e}")
    
    return config

def main():
    """Entry point for verification."""
    try:
        config = get_data_source_config()
        logging.getLogger("verify_source").info("Source verified successfully.")
        return 0
    except RuntimeError as e:
        logging.getLogger("verify_source").error(str(e))
        return 1
    except Exception as e:
        logging.getLogger("verify_source").error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
