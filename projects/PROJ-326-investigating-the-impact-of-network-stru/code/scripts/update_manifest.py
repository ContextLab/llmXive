import argparse
import logging
import sys
from pathlib import Path

from code.src.generators.manifest_updater import main as update_manifest_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Update the global batch manifest with stratification summary."
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/raw/global_batch_manifest.json",
        help="Path to the manifest file."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the config file."
    )
    
    args = parser.parse_args()
    
    try:
        # Note: The main function in manifest_updater.py will handle loading
        # We can extend it to accept paths if needed, but for now we use defaults
        # or we can modify the main function to accept arguments
        update_manifest_main()
    except Exception as e:
        logging.error(f"Failed to update manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
