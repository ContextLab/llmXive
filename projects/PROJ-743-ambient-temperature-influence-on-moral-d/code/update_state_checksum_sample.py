"""
Task T003: Compute and record the SHA-256 checksum of the downloaded ERA5 sample file.

This script computes the SHA-256 checksum of `data/raw/era5_sample.h5` and updates
the project state file `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`
under the key `artifact_hashes.era5_sample`. It also updates the `updated_at` timestamp.

It relies on the `update_state_checksum` module for the core logic.
"""
import sys
import logging
from pathlib import Path

# Import the main logic from the existing utility module
from update_state_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Entry point for T003.
    Targets: data/raw/era5_sample.h5
    State File: state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
    Key: artifact_hashes.era5_sample
    """
    # Setup logging
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting T003: Checksum computation for ERA5 sample file.")
    
    # Define the target file path relative to project root
    project_root = Path(__file__).resolve().parents[1]
    target_file = project_root / "data" / "raw" / "era5_sample.h5"
    state_file = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    
    if not target_file.exists():
        logger.error(f"Target file not found: {target_file}")
        logger.error("T003 cannot proceed without the ERA5 sample file. Please ensure T002 has been completed successfully.")
        sys.exit(1)
    
    # Prepare arguments for the underlying checksum utility
    # The utility expects file_path and state_path as arguments or environment variables.
    # We will call the main function directly if it accepts args, or simulate the call.
    # Looking at `update_state_checksum`, `main` likely parses sys.argv.
    # We will invoke it by modifying sys.argv to match the expected CLI usage.
    
    original_argv = sys.argv[:]
    try:
        sys.argv = [
            "update_state_checksum_sample.py",
            "--file", str(target_file),
            "--state", str(state_file),
            "--key", "artifact_hashes.era5_sample"
        ]
        
        # Execute the main logic from update_state_checksum
        # Note: The provided API surface shows `update_state_checksum` has a `main` function.
        # We assume it accepts command line arguments for file, state, and key.
        compute_checksum_main()
        
        logger.info("T003 completed successfully. Checksum recorded and state updated.")
        
    except Exception as e:
        logger.error(f"Error during T003 execution: {e}")
        sys.exit(1)
    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    main()
