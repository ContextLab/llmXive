import sys
import logging
from pathlib import Path

# Import the core logic from the sibling module
from update_state_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Entry point for T003: Compute and record the SHA-256 checksum of the downloaded
    ERA5 sample file (data/raw/era5_sample.h5) in the project state YAML.
    """
    logger = setup_logging()
    logger.info("Starting T003: Checksum computation for ERA5 sample file.")

    # Define the specific input file path for the sample
    input_file_path = Path("data/raw/era5_sample.h5")
    
    # Define the state file path
    state_file_path = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")

    if not input_file_path.exists():
        logger.error(f"Input file not found: {input_file_path}. Task T003 cannot proceed.")
        sys.exit(1)

    try:
        # Call the generic main logic, passing specific arguments if the function signature allows,
        # or rely on the generic function to handle the path if it's hardcoded or env-based.
        # Since the existing API `update_state_checksum.main` likely takes no args or sys.argv,
        # we will assume it handles the logic or we need to wrap it.
        # Looking at the API surface: `from update_state_checksum import compute_sha256, update_state_file, main`
        # The `main` function in `update_state_checksum` is likely the entry point for the full run.
        # For T003, we need to target the *sample* file specifically.
        # We will invoke the core functions directly to ensure the correct file is processed.
        
        # Compute checksum
        checksum = compute_checksum_main(input_file_path) # Assuming main returns checksum or we use compute_sha256
        # Actually, let's look at the imports again.
        # `from update_state_checksum import main` -> likely a script runner.
        # `from update_state_checksum import compute_sha256` -> likely the function.
        
        # Let's re-implement the specific logic here to ensure T003 requirements are met exactly,
        # using the helper functions from `update_state_checksum`.
        
        checksum_value = compute_sha256(input_file_path)
        logger.info(f"Computed SHA-256 for {input_file_path}: {checksum_value}")

        # Update the state file
        update_state_file(
            state_file_path=state_file_path,
            artifact_key="era5_sample",
            checksum=checksum_value
        )
        
        logger.info("T003 completed successfully. State file updated.")
        
    except Exception as e:
        logger.error(f"Error during T003 execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
