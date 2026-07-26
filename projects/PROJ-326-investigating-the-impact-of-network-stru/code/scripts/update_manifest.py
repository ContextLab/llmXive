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
    parser = argparse.ArgumentParser(
        description="Update the global batch manifest with stratification summary."
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/raw/global_batch_manifest.json",
        help="Path to the global batch manifest JSON file."
    )
    
    args = parser.parse_args()
    
    # Temporarily override sys.argv to pass the manifest path to the main function
    # The main function in manifest_updater expects the path as the first argument
    original_argv = sys.argv
    sys.argv = ["update_manifest", args.manifest]
    
    try:
        update_manifest_main()
    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    setup_logging()
    main()
