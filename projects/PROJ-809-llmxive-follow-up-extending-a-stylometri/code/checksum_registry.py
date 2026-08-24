"""
T016: Write checksums of raw download and processed artifacts to state file.

This script computes SHA-256 checksums for:
1. Raw download: data/raw/arxiv_subset.parquet
2. Processed artifacts: data/processed/ (author folders and collision_report.json)

It updates the state file at state/PROJ-809-llmxive-followup.yaml
"""
import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from update_state import load_state, save_state, hash_artifact, register_artifact, update_artifact_hash
from utils import get_logger, ensure_dir, compute_sha256

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_FILE = PROJECT_ROOT / "state" / "PROJ-809-llmxive-followup.yaml"
COLLISION_REPORT = DATA_PROCESSED_DIR / "collision_report.json"

logger = get_logger(__name__)

def get_raw_artifact_path() -> Path:
    """Locate the raw arxiv parquet file."""
    if DATA_RAW_DIR.exists():
        parquet_files = list(DATA_RAW_DIR.glob("*.parquet"))
        if parquet_files:
            # Expecting exactly one based on T011
            return parquet_files[0]
    raise FileNotFoundError(f"No .parquet file found in {DATA_RAW_DIR}")

def get_processed_artifact_paths() -> List[Path]:
    """Locate all processed artifacts (author files and collision report)."""
    artifacts = []
    
    # Check for collision report
    if COLLISION_REPORT.exists():
        artifacts.append(COLLISION_REPORT)
    
    # Check author folders
    if DATA_PROCESSED_DIR.exists():
        for item in DATA_PROCESSED_DIR.iterdir():
            if item.is_dir():
                # Collect all files in the author folder
                for file_path in item.rglob("*"):
                    if file_path.is_file():
                        artifacts.append(file_path)
            elif item.is_file() and item != COLLISION_REPORT:
                # Root level files in processed (if any)
                artifacts.append(item)
    
    return sorted(artifacts)

def main():
    """
    Main entry point for T016.
    Computes checksums and updates the state file.
    """
    logger.info("Starting T016: Checksum Registration")
    
    # Ensure state directory exists
    ensure_dir(STATE_FILE.parent)

    # 1. Process Raw Artifact
    try:
        raw_path = get_raw_artifact_path()
        logger.info(f"Found raw artifact: {raw_path}")
        raw_hash = compute_sha256(str(raw_path))
        logger.info(f"Raw artifact SHA-256: {raw_hash}")
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot proceed without raw data. Did T011 run successfully?")
        return 1

    # 2. Process Processed Artifacts
    processed_paths = get_processed_artifact_paths()
    if not processed_paths:
        logger.warning("No processed artifacts found in data/processed/. "
                     "Ensure T014 and T013a have run successfully.")
    
    processed_hashes = {}
    for p in processed_paths:
        rel_path = p.relative_to(PROJECT_ROOT)
        h = compute_sha256(str(p))
        processed_hashes[str(rel_path)] = h
        logger.info(f"Processed artifact: {rel_path} -> {h[:16]}...")

    # 3. Update State File
    logger.info(f"Updating state file: {STATE_FILE}")
    state = load_state(STATE_FILE)
    
    # Register/Update Raw Artifact
    register_artifact(
        state, 
        artifact_name="raw_arxiv_subset", 
        path=str(raw_path.relative_to(PROJECT_ROOT)), 
        hash=raw_hash,
        description="Raw arXiv dataset subset (parquet)"
    )

    # Register/Update Processed Artifacts
    for rel_path_str, h in processed_hashes.items():
        artifact_name = f"processed_{Path(rel_path_str).stem}"
        if Path(rel_path_str).suffix == '.json':
            artifact_name = f"processed_{Path(rel_path_str).stem}"
        elif Path(rel_path_str).is_dir():
            artifact_name = f"processed_author_{Path(rel_path_str).stem}"
        
        register_artifact(
            state,
            artifact_name=artifact_name,
            path=rel_path_str,
            hash=h,
            description=f"Processed artifact: {rel_path_str}"
        )

    # Save state
    save_state(state, STATE_FILE)
    logger.info("State file updated successfully.")

    # Verification summary
    logger.info("Checksum Registry Summary:")
    logger.info(f"  - Raw files registered: 1")
    logger.info(f"  - Processed files registered: {len(processed_hashes)}")
    logger.info(f"  - State file: {STATE_FILE}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
