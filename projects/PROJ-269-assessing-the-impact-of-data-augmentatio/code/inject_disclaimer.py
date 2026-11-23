"""
T030: Inject disclaimer into all result JSON files and update manifest.

This script discovers all JSON files in the results/ directory (baseline,
augmented, and summary reports), ensures a 'metadata' object exists, and
injects the required disclaimer string into 'metadata.disclaimer'. It then
computes the SHA256 checksum of the modified file and appends the hash to
the state manifest.

FR-007 Compliance: "Findings are associational, not causal..."
"""
import os
import json
import hashlib
import logging
import glob
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DISCLAIMER_STRING = "DISCLAIMER: Findings are associational, not causal. This study assesses statistical power under specific simulation conditions and does not establish causal relationships in real-world clinical settings."
RESULTS_GLOB_PATTERN = "results/**/*.json"
MANIFEST_PATH = "data/derived/state_manifest.json"
DISAVOWER_LOG_PATH = "data/derived/disclaimer_injection.log"

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def inject_disclaimer_into_file(file_path: str) -> bool:
    """
    Inject disclaimer into the metadata section of a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        True if modification was successful, False otherwise.
    """
    try:
        # Read existing content
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ensure metadata object exists
        if 'metadata' not in data:
            data['metadata'] = {}

        # Inject disclaimer
        data['metadata']['disclaimer'] = DISCLAIMER_STRING

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Injected disclaimer into: {file_path}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")
        return False

def append_to_manifest(file_path: str, sha256_hash: str) -> None:
    """
    Append the file hash to the state manifest.

    Args:
        file_path: Path to the processed file.
        sha256_hash: SHA256 hash of the modified file.
    """
    manifest_data = {}
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing manifest: {e}. Starting fresh.")
            manifest_data = {}

    if 'disclaimer_injection' not in manifest_data:
        manifest_data['disclaimer_injection'] = []

    manifest_entry = {
        "file": file_path,
        "sha256": sha256_hash,
        "timestamp": None  # Timestamps are usually added by the runner, but we can add a placeholder or skip
    }
    
    # Avoid duplicates if run multiple times (optional, but good practice)
    if not any(entry['file'] == file_path for entry in manifest_data['disclaimer_injection']):
        manifest_data['disclaimer_injection'].append(manifest_entry)

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Appended hash for {file_path} to manifest.")

def main():
    """Main entry point for T030."""
    logger.info("Starting T030: Disclaimer Injection")

    # Ensure results directory exists
    results_dir = Path("results")
    if not results_dir.exists():
        logger.error("Results directory 'results/' not found. Aborting.")
        return

    # Discover all JSON files
    json_files = glob.glob(str(results_dir / RESULTS_GLOB_PATTERN), recursive=True)
    
    if not json_files:
        logger.warning("No JSON files found in results/ directory.")
        return

    logger.info(f"Found {len(json_files)} JSON files to process.")

    success_count = 0
    fail_count = 0

    for file_path in json_files:
        if inject_disclaimer_into_file(file_path):
            sha256 = compute_sha256(file_path)
            append_to_manifest(file_path, sha256)
            success_count += 1
        else:
            fail_count += 1

    logger.info(f"Completed T030. Success: {success_count}, Failed: {fail_count}")

    # Log summary to derived log
    with open(DISAVOWER_LOG_PATH, 'w', encoding='utf-8') as f:
        f.write(f"T030 Disclaimer Injection Summary\n")
        f.write(f"Total files processed: {len(json_files)}\n")
        f.write(f"Successful injections: {success_count}\n")
        f.write(f"Failed injections: {fail_count}\n")

    if fail_count > 0:
        logger.warning(f"{fail_count} files failed to process. Check logs for details.")

if __name__ == "__main__":
    main()