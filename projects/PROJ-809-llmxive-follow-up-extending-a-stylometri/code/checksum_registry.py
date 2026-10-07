import os
import sys
import json
import logging
import hashlib
from pathlib import Path

from config import load_config, save_config, ensure_dir
from utils import compute_sha256, get_logger
from update_state import load_state, save_state, register_artifact

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
STATE_PATH = PROJECT_ROOT / "state" / "PROJ-809-llmxive-followup.yaml"

# Data paths based on T011-T015 execution
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "arxiv_subset.parquet"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

logger = get_logger(__name__)

def get_raw_artifact_path() -> Path:
    return RAW_DATA_PATH

def get_processed_artifact_paths() -> list[Path]:
    """Returns list of processed artifacts (author folders + collision report)."""
    processed_files = []
    if not PROCESSED_DIR.exists():
        logger.warning(f"Processed directory {PROCESSED_DIR} does not exist yet.")
        return processed_files

    # Check for author folders (expected format: author_<id>)
    author_dirs = [d for d in PROCESSED_DIR.iterdir() if d.is_dir() and d.name.startswith("author_")]
    for d in author_dirs:
        # Assuming text files inside
        txt_files = list(d.glob("*.txt"))
        if txt_files:
            processed_files.extend(txt_files)

    # Check for collision report
    collision_report = PROCESSED_DIR / "collision_report.json"
    if collision_report.exists():
        processed_files.append(collision_report)

    return processed_files

def main():
    """
    T016 Implementation: Write checksums of raw download and processed artifacts
    to state/PROJ-809-llmxive-followup.yaml (Constitution III & V).
    """
    setup_logging()
    logger.info("Starting T016: Checksum Registry and State Update")

    # Ensure state directory exists
    ensure_dir(STATE_PATH.parent)

    # 1. Hash Raw Artifact
    raw_path = get_raw_artifact_path()
    raw_hash = None
    if raw_path.exists():
        raw_hash = compute_sha256(raw_path)
        logger.info(f"Raw artifact found: {raw_path} | SHA256: {raw_hash}")
    else:
        logger.error(f"Raw artifact NOT FOUND: {raw_path}. Cannot proceed without raw data.")
        # We fail loudly as per constraints if the primary data is missing
        # However, the task is to write checksums. If the file is missing, we record that state.
        # But per T011, the file should exist. If it doesn't, the pipeline is broken.
        # We will attempt to continue with what we have, but log the error.
        return 1

    # 2. Hash Processed Artifacts
    processed_files = get_processed_artifact_paths()
    processed_hashes = {}
    if not processed_files:
        logger.warning("No processed artifacts found to hash. Did T012-T015 run successfully?")
    else:
        for p_file in processed_files:
            p_hash = compute_sha256(p_file)
            # Use relative path for state file
            rel_path = p_file.relative_to(PROJECT_ROOT)
            processed_hashes[str(rel_path)] = p_hash
        logger.info(f"Processed {len(processed_files)} artifacts.")

    # 3. Update State File
    # Load existing state or create new
    state = load_state(STATE_PATH)
    
    # Register artifacts
    state["artifacts"]["raw"]["arxiv_subset_parquet"] = {
        "path": str(raw_path.relative_to(PROJECT_ROOT)),
        "sha256": raw_hash,
        "last_updated": str(Path(raw_path).stat().st_mtime)
    }

    state["artifacts"]["processed"] = {
        "files": processed_hashes,
        "count": len(processed_hashes),
        "last_updated": str(Path(PROCESSED_DIR).stat().st_mtime)
    }

    # Update metadata
    state["metadata"]["last_checksum_run"] = str(Path(PROJECT_ROOT).stat().st_mtime)
    state["metadata"]["constitution_v_compliance"] = True

    save_state(state, STATE_PATH)
    logger.info(f"State file updated at {STATE_PATH}")
    logger.info("T016 Complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
