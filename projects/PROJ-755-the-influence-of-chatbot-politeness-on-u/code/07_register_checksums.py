import os
import sys
import logging
from pathlib import Path

# Add project root to path to ensure imports work regardless of CWD
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.checksum_registry import register_raw_data_checksum, get_raw_data_checksums
from utils.data_integrity import compute_file_checksum

logger = logging.getLogger(__name__)

def main():
    """
    Implements T007b: Update state YAML to record checksums in artifact_hashes.raw_data.
    
    This script scans the data/raw directory for available parquet files, computes their
    SHA256 checksums, and updates the project state YAML file at:
    state/projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml
    
    The checksums are recorded under the 'artifact_hashes.raw_data' key.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml"
    raw_data_dir = project_root / "data" / "raw"

    if not state_file.exists():
        logger.error(f"State file not found: {state_file}")
        sys.exit(1)

    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory not found: {raw_data_dir}. No checksums to register.")
        return

    logger.info(f"Scanning for raw data files in: {raw_data_dir}")
    
    # Collect all parquet files recursively
    parquet_files = list(raw_data_dir.rglob("*.parquet"))
    
    if not parquet_files:
        logger.warning("No .parquet files found in data/raw. Skipping checksum registration.")
        return

    checksums = {}
    for file_path in parquet_files:
        try:
            rel_path = file_path.relative_to(project_root)
            checksum = compute_file_checksum(file_path)
            checksums[str(rel_path)] = checksum
            logger.info(f"Computed checksum for {rel_path}: {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
            # Continue with other files rather than failing the whole run

    if not checksums:
        logger.warning("No checksums were successfully computed.")
        return

    # Register checksums in the state file
    # The register_raw_data_checksum function handles loading, updating, and saving
    try:
        register_raw_data_checksum(checksums)
        logger.info(f"Successfully updated state file: {state_file}")
        logger.info(f"Registered {len(checksums)} raw data artifacts.")
        
        # Verify the update
        current_checksums = get_raw_data_checksums()
        logger.debug(f"Verification - Current registered checksums: {current_checksums}")
        
    except Exception as e:
        logger.error(f"Failed to update state file with checksums: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
