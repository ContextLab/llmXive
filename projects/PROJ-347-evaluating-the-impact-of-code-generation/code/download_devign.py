"""
Download and prepare the vulnerable code dataset.

As the original Juliet/Devign URLs are unavailable, this script uses the 
CodeXGLUE vulnerability dataset from HuggingFace, which is a verified 
alternative specified in the project's research requirements.
"""
import hashlib
import json
import sys
from pathlib import Path
import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Destination locations
CSV_DEST = paths.data("raw", "devign", "devign.csv")
CHECKSUMS_PATH = paths.data("checksums.json")

def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_checksums(path: Path) -> dict:
    """Load a JSON checksum mapping; return empty dict if file missing."""
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_checksums(path: Path, data: dict) -> None:
    """Write checksum mapping to JSON (pretty‑printed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def main() -> None:
    """
    Fetch the CodeXGLUE vulnerability dataset and save it as the Devign stand-in.
    """
    # Step 0: Short-circuit if file exists and checksum matches
    if CSV_DEST.is_file():
        existing_checksum = compute_sha256(CSV_DEST)
        checksums = load_checksums(CHECKSUMS_PATH)
        if checksums.get(str(CSV_DEST)) == existing_checksum:
            log.info("Dataset already present and verified. Skipping download.")
            return

    log.info("Downloading CodeXGLUE vulnerability dataset from HuggingFace...")
    try:
        # Load the 'vuln' configuration of CodeXGLUE
        dataset = load_dataset("code_x_glue", "vuln", split="train")
        df = dataset.to_pandas()
        
        # Ensure the directory exists
        CSV_DEST.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(CSV_DEST, index=False)
        log.info(f"Saved dataset to {CSV_DEST}")
        
        # Record checksum
        checksum = compute_sha256(CSV_DEST)
        checksums = load_checksums(CHECKSUMS_PATH)
        checksums[str(CSV_DEST)] = checksum
        save_checksums(CHECKSUMS_PATH, checksums)
        log.info(f"Recorded checksum: {checksum}")
        
    except Exception as e:
        log.exception(f"Failed to download dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
