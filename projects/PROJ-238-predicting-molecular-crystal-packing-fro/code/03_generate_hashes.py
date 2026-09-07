"""
Task T018: Generate SHA-256 checksums for raw CIFs and all derived CSV/JSON artifacts.
Records them in state/projects/PROJ-238.../artifact_hashes.
"""
import hashlib
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Iterable

# Import logging setup from config to match project style
from code.config import setup_logging, log_event

# Define project root and state directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-238-predicting-molecular-crystal-packing-fro"
HASHES_FILE = STATE_DIR / "artifact_hashes"

# Define target directories to scan for artifacts
# Based on tasks.md and pipeline outputs:
# - data/raw/ (CIFs, sample IDs)
# - data/descriptors/ (raw_descriptors.csv, derived.csv)
# - data/processed/ (train.csv, val.csv, test.csv, logs, split_report.json)
# - results/ (metrics.json, feature_importance.png, sensitivity_report.md, etc.)
TARGET_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "descriptors",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "results",
]

# Extensions to include
TARGET_EXTENSIONS = {".cif", ".csv", ".json", ".log", ".md", ".txt", ".png"}

logger = setup_logging()

def iter_target_files() -> Iterable[Path]:
    """Iterate over all target files in the defined directories."""
    for dir_path in TARGET_DIRS:
        if not dir_path.exists():
            logger.warning(f"Target directory does not exist: {dir_path}")
            continue
        for ext in TARGET_EXTENSIONS:
            for file_path in dir_path.glob(f"*{ext}"):
                if file_path.is_file():
                    yield file_path

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def collect_hashes() -> List[Dict[str, Any]]:
    """Collect hashes for all target files."""
    hashes = []
    for file_path in iter_target_files():
        try:
            hash_val = compute_sha256(file_path)
            # Store relative path from project root for portability
            rel_path = file_path.relative_to(PROJECT_ROOT)
            hashes.append({
                "path": str(rel_path),
                "sha256": hash_val,
                "size_bytes": file_path.stat().st_size
            })
            logger.info(f"Hashed: {rel_path}")
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
    return hashes

def write_hash_file(hashes: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the collected hashes to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "project_id": "PROJ-238-predicting-molecular-crystal-packing-fro",
        "generated_at": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip(),
        "file_count": len(hashes),
        "files": hashes
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Wrote {len(hashes)} hashes to {output_path}")

def main() -> int:
    """Main entry point."""
    logger.info("Starting artifact hash generation for T018")
    hashes = collect_hashes()
    if not hashes:
        logger.warning("No files found to hash. Check TARGET_DIRS and TARGET_EXTENSIONS.")
        # Still create the file to indicate completion, even if empty
    write_hash_file(hashes, HASHES_FILE)
    log_event("T018_hash_generation", {"file_count": len(hashes)})
    return 0

if __name__ == "__main__":
    exit(main())
