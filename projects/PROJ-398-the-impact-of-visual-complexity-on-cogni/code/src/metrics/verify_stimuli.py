"""
Verify downloaded stimuli by computing SHA-256 checksums and recording them.

This script reads the stimuli downloaded by T014 from `data/stimuli/`,
computes a SHA-256 checksum for each file, and records the results in
`state/artifact_hashes.json`.

It relies on `src/lib/utils.py` for the checksum computation logic.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure the project root is in the path to allow relative imports
# This script is expected to be run from the project root or code directory
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lib.utils import compute_file_checksum

STIMULI_DIR = project_root / "data" / "stimuli"
STATE_DIR = project_root / "state"
HASHES_FILE = STATE_DIR / "artifact_hashes.json"

def verify_stimuli() -> Dict[str, Any]:
    """
    Iterate over all files in the stimuli directory, compute their SHA-256 checksums,
    and save the mapping to state/artifact_hashes.json.
    
    Returns:
        Dict containing the number of files processed and the path to the output file.
    """
    if not STIMULI_DIR.exists():
        raise FileNotFoundError(
            f"Stimuli directory not found at {STIMULI_DIR}. "
            "Please ensure T014 (fetch_stimuli) has been executed successfully."
        )

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    file_hashes = {}
    files_processed = 0

    # Walk through the stimuli directory to find all image files
    # Assuming standard image extensions based on the dataset nature
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    for root, _, files in os.walk(STIMULI_DIR):
        for file_name in files:
            if any(file_name.lower().endswith(ext) for ext in valid_extensions):
                file_path = Path(root) / file_name
                
                try:
                    checksum = compute_file_checksum(file_path)
                    # Use relative path from stimuli dir for cleaner storage
                    relative_path = file_path.relative_to(STIMULI_DIR)
                    file_hashes[str(relative_path)] = checksum
                    files_processed += 1
                except Exception as e:
                    print(f"Error computing checksum for {file_path}: {e}", file=sys.stderr)

    if files_processed == 0:
        print("Warning: No valid image files found in the stimuli directory.", file=sys.stderr)

    # Save the results to the state file
    output_data = {
        "source_directory": str(STIMULI_DIR),
        "algorithm": "sha256",
        "file_count": files_processed,
        "hashes": file_hashes
    }

    with open(HASHES_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Successfully verified {files_processed} stimuli.")
    print(f"Checksums saved to: {HASHES_FILE}")

    return output_data

def main():
    """Entry point for the script."""
    try:
        verify_stimuli()
    except Exception as e:
        print(f"Verification failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
