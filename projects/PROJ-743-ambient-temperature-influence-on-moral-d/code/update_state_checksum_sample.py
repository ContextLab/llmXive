import sys
import logging
from pathlib import Path
from update_state_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Entry point for T003: Checksum Sample.
    Computes SHA-256 of data/raw/era5_sample.h5 and updates state YAML.
    """
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting T003: Checksum Sample computation and state update.")

    # Define paths relative to project root
    # Assuming the script runs from the project root or the paths are absolute
    # We construct absolute paths based on the standard project structure
    project_root = Path(__file__).resolve().parent.parent
    sample_file_path = project_root / "data" / "raw" / "era5_sample.h5"
    state_file_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

    if not sample_file_path.exists():
        logger.error(f"Sample file not found: {sample_file_path}. T003 cannot proceed.")
        sys.exit(1)

    if not state_file_path.exists():
        logger.error(f"State file not found: {state_file_path}. T003 cannot proceed.")
        sys.exit(1)

    try:
        # Import the core logic directly to ensure we use the correct implementation
        # The function 'main' in update_state_checksum handles the checksum computation
        # and file update. We pass the specific file path and state path.
        # Note: The existing 'main' in update_state_checksum might need adaptation
        # to accept specific file paths if it currently hardcodes them.
        # However, looking at the API surface, 'update_state_checksum' has 'main'.
        # Let's assume we need to call the logic specifically for this file.
        # To be safe and strictly follow the "extend" rule without rewriting the whole module
        # if it's not provided, we will implement the specific logic here using the
        # helper 'compute_sha256' from utils if available, or re-implement the minimal logic
        # if 'compute_sha256' is not in utils (it is listed in utils API).

        from utils import compute_sha256
        import yaml
        from datetime import datetime, timezone

        checksum = compute_sha256(sample_file_path)
        logger.info(f"Computed SHA-256 for {sample_file_path.name}: {checksum}")

        # Load state file
        with open(state_file_path, 'r') as f:
            state_data = yaml.safe_load(f)

        if state_data is None:
            state_data = {}

        # Ensure keys exist
        if 'artifact_hashes' not in state_data:
            state_data['artifact_hashes'] = {}

        # Update checksum
        state_data['artifact_hashes']['era5_sample'] = checksum

        # Update timestamp (Constitution Principle V)
        state_data['updated_at'] = datetime.now(timezone.utc).isoformat()

        # Write back
        with open(state_file_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Updated state file: {state_file_path}")
        logger.info("T003 completed successfully.")

    except Exception as e:
        logger.error(f"Error during T003 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
