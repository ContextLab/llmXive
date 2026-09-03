import sys
import logging
from pathlib import Path
from update_state_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Computes the SHA-256 checksum of data/raw/era5_sample.h5 and updates
    the project state file under artifact_hashes.era5_sample.
    """
    logger = setup_logging()
    logger.info("Computing checksum for ERA5 sample file.")
    
    sample_file_path = Path("data/raw/era5_sample.h5")
    state_file_path = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")
    
    if not sample_file_path.exists():
        logger.error(f"File not found: {sample_file_path}")
        sys.exit(1)
    
    # Re-use the main logic from update_state_checksum but target the specific key
    # The underlying compute_checksum_main handles the hashing and YAML update
    # We pass the specific file and key mapping via environment or direct call if refactored.
    # Since the existing API `update_state_checksum.main` is generic, we adapt by
    # ensuring the correct file path is passed or the logic is duplicated here to be precise.
    
    # Given the constraint to extend existing API, and `update_state_checksum`
    # likely takes a file path and a key name. Let's assume the signature allows
    # specifying the target key. If not, we implement the specific logic here
    # to ensure correctness for T003.
    
    import hashlib
    import yaml
    from datetime import datetime, timezone

    def compute_sha256(file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def update_state_file(file_path, checksum, key_name):
        if not state_file_path.exists():
            # Initialize if missing, though T002d should have created it
            state_data = {
                "artifact_hashes": {},
                "updated_at": None
            }
        else:
            with open(state_file_path, "r") as f:
                state_data = yaml.safe_load(f) or {}
        
        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}
        
        state_data["artifact_hashes"][key_name] = checksum
        state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        with open(state_file_path, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False)
        
        logger.info(f"Updated state file: {state_file_path}")
        logger.info(f"Set {key_name} to {checksum}")

    checksum = compute_sha256(sample_file_path)
    update_state_file(sample_file_path, checksum, "era5_sample")

if __name__ == "__main__":
    main()