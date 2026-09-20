import hashlib
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root and target state directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-238-predicting-molecular-crystal-packing-fro"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Target files to hash (relative to project root)
TARGET_FILES = [
    "data/raw/cod_sample_ids.txt",
    "data/raw/volume_validation.log",
    "data/descriptors/raw_descriptors.csv",
    "data/processed/hydrogen_addition.log",
    "data/processed/filter_log.txt",
    "data/processed/missing_target.log",
    "data/processed/train.csv",
    "data/processed/val.csv",
    "data/processed/test.csv",
    "data/processed/split_validation.log",
    "data/processed/split_report.json",
    "results/metrics.json",
    "results/feature_importance.png",
    "results/sensitivity_report.md",
    "results/control_analysis_metrics.json",
    "data/interactions/raw_interactions.csv",
    "data/interactions/interaction_classification.csv",
    "results/interaction_classification.md",
]

def iter_target_files() -> List[Path]:
    """Yield paths to target files that exist."""
    existing = []
    for rel_path in TARGET_FILES:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            existing.append(full_path)
        else:
            logger.warning(f"Target file not found, skipping: {full_path}")
    return existing

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None

def collect_hashes(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """Collect hashes for a list of file paths."""
    hashes = []
    for file_path in file_paths:
        rel_path = file_path.relative_to(PROJECT_ROOT)
        digest = compute_sha256(file_path)
        if digest:
            hashes.append({
                "path": str(rel_path),
                "sha256": digest,
                "size_bytes": file_path.stat().st_size
            })
    return hashes

def write_hash_file(hashes: List[Dict[str, Any]], output_path: Path):
    """Write collected hashes to a JSON file."""
    output_content = {
        "project_id": "PROJ-238-predicting-molecular-crystal-packing-fro",
        "artifact_hashes": hashes
    }
    with open(output_path, "w") as f:
        json.dump(output_content, f, indent=2)
    logger.info(f"Hash file written to {output_path}")

def main():
    logger.info("Starting artifact hash generation...")
    target_files = iter_target_files()
    if not target_files:
        logger.error("No target files found to hash.")
        return

    hashes = collect_hashes(target_files)
    output_path = STATE_DIR / "artifact_hashes"
    write_hash_file(hashes, output_path)
    logger.info(f"Successfully updated {output_path} with {len(hashes)} artifact hashes.")

if __name__ == "__main__":
    main()
